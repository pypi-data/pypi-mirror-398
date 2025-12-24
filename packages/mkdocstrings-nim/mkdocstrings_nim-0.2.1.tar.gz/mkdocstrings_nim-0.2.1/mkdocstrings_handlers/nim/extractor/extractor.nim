## AST extraction logic for nimdocinfo
import std/[json, strutils, sequtils, os]
import compiler/[ast, parser, idents, options, pathutils, lineinfos, msgs, renderer, llstream]

type
  FieldInfo* = object
    name*: string
    typ*: string
    doc*: string
    exported*: bool
    branch*: string  ## Empty or "when kind = x" for case objects

  DocEntry* = object
    name*: string
    kind*: string
    line*: int
    signature*: string
    params*: seq[tuple[name, typ: string]]
    returns*: string
    pragmas*: seq[string]
    raises*: seq[string]
    doc*: string
    exported*: bool  ## True if symbol has * (public API)
    fields*: seq[FieldInfo]  ## For object/ref object types
    values*: seq[FieldInfo]  ## For enum types

  ModuleDoc* = object
    module*: string
    file*: string
    doc*: string
    entries*: seq[DocEntry]

proc extractDocComment(n: PNode): string =
  ## Extract doc comment from a node
  if n == nil:
    return ""
  if n.comment.len > 0:
    return n.comment.strip
  return ""

proc extractPragmas(n: PNode): seq[string] =
  ## Extract pragma names from a pragma node
  result = @[]
  if n == nil or n.kind != nkPragma:
    return
  for child in n:
    if child.kind == nkIdent:
      result.add($child.ident.s)
    elif child.kind == nkExprColonExpr and child[0].kind == nkIdent:
      result.add($child[0].ident.s)

proc extractRaises(n: PNode): seq[string] =
  ## Extract exception types from raises pragma
  ## e.g., {.raises: [ValueError, IOError].}
  result = @[]
  if n == nil or n.kind != nkPragma:
    return
  for child in n:
    if child.kind == nkExprColonExpr and child.len >= 2:
      if child[0].kind == nkIdent and $child[0].ident.s == "raises":
        let bracket = child[1]
        if bracket.kind == nkBracket:
          for exc in bracket:
            if exc.kind == nkIdent:
              result.add($exc.ident.s)
            elif exc.kind == nkDotExpr:
              # Handle qualified names like system.Exception
              result.add($exc)

proc extractParams(n: PNode): seq[tuple[name, typ: string]] =
  ## Extract parameter list from formal params
  result = @[]
  if n == nil or n.kind != nkFormalParams:
    return
  # Skip first child (return type)
  for i in 1..<n.len:
    let param = n[i]
    if param.kind == nkIdentDefs:
      let typNode = param[^2]
      let typStr = if typNode.kind == nkEmpty: "auto" else: $typNode
      # All names except last two (type and default)
      for j in 0..<param.len - 2:
        if param[j].kind == nkIdent:
          result.add(($param[j].ident.s, typStr))

proc extractReturnType(n: PNode): string =
  ## Extract return type from formal params
  if n == nil or n.kind != nkFormalParams or n.len == 0:
    return ""
  let retNode = n[0]
  if retNode.kind == nkEmpty:
    return ""
  return $retNode

const
  # Nim AST indices for routine (proc/func/etc) nodes
  routineNameIdx = 0
  routinePatternIdx = 1
  routineGenericParamsIdx = 2
  routineParamsIdx = 3
  routinePragmasIdx = 4
  routineBodyIdx = 6

proc renderSignature(n: PNode, kind: string, name: string): string =
  ## Render full signature as string
  result = kind & " " & name
  if n.len > routineParamsIdx and n[routineParamsIdx].kind == nkFormalParams:
    let params = n[routineParamsIdx]
    var paramStrs: seq[string] = @[]
    for i in 1..<params.len:
      paramStrs.add($params[i])
    result &= "(" & paramStrs.join("; ") & ")"
    let ret = extractReturnType(n[routineParamsIdx])
    if ret.len > 0:
      result &= ": " & ret

proc isExported(n: PNode): bool =
  ## Check if a name node represents an exported symbol (has *)
  n.kind == nkPostfix

proc extractName(n: PNode): string =
  ## Extract name from a name node (handles postfix for exported symbols)
  if n.kind == nkIdent:
    return $n.ident.s
  elif n.kind == nkPostfix and n.len >= 2 and n[1].kind == nkIdent:
    return $n[1].ident.s
  elif n.kind == nkPostfix and n.len >= 2 and n[1].kind == nkAccQuoted:
    # Handle quoted operators like `+`*
    if n[1].len > 0 and n[1][0].kind == nkIdent:
      return $n[1][0].ident.s
  return ""

proc extractObjectFields(recList: PNode, branch: string = ""): seq[FieldInfo] =
  ## Extract fields from an object's record list
  result = @[]
  if recList == nil:
    return

  for child in recList:
    case child.kind
    of nkIdentDefs:
      # Field: name*: Type ## doc
      let typNode = child[^2]
      let typ = if typNode.kind == nkEmpty: "" else: $typNode
      let doc = extractDocComment(child)
      # All names except last two (type and default value)
      for i in 0..<child.len - 2:
        let nameNode = child[i]
        result.add FieldInfo(
          name: extractName(nameNode),
          typ: typ,
          doc: doc,
          exported: isExported(nameNode),
          branch: branch
        )
    of nkRecCase:
      # Case object: discriminator + branches
      # First child is the discriminator (nkIdentDefs)
      if child.len > 0 and child[0].kind == nkIdentDefs:
        let discriminator = child[0]
        let typNode = discriminator[^2]
        let typ = if typNode.kind == nkEmpty: "" else: $typNode
        let doc = extractDocComment(discriminator)
        for i in 0..<discriminator.len - 2:
          let nameNode = discriminator[i]
          result.add FieldInfo(
            name: extractName(nameNode),
            typ: typ,
            doc: doc,
            exported: isExported(nameNode),
            branch: ""  # Discriminator has no branch
          )
      # Remaining children are branches
      for i in 1..<child.len:
        let branchNode = child[i]
        case branchNode.kind
        of nkOfBranch:
          # nkOfBranch: [condition(s), nkRecList]
          let branchCond = "when " & $branchNode[0]
          if branchNode.len > 1:
            let branchFields = extractObjectFields(branchNode[^1], branchCond)
            for f in branchFields:
              result.add f
        of nkElse:
          # nkElse: [nkRecList]
          if branchNode.len > 0:
            let branchFields = extractObjectFields(branchNode[0], "else")
            for f in branchFields:
              result.add f
        else:
          discard
    of nkRecList:
      # Nested record list
      let nested = extractObjectFields(child, branch)
      for f in nested:
        result.add f
    else:
      discard

proc extractEnumValues(enumDef: PNode): seq[FieldInfo] =
  ## Extract values from an enum definition
  result = @[]
  if enumDef == nil or enumDef.kind != nkEnumTy:
    return

  for child in enumDef:
    case child.kind
    of nkEnumFieldDef:
      # Enum value with explicit value: name = value
      let nameNode = child[0]
      let valueNode = if child.len > 1: child[1] else: nil
      result.add FieldInfo(
        name: extractName(nameNode),
        typ: if valueNode != nil: $valueNode else: "",
        doc: extractDocComment(child),
        exported: true,  # enum values always public
        branch: ""
      )
    of nkIdent:
      # Simple enum value without explicit value
      result.add FieldInfo(
        name: $child.ident.s,
        typ: "",
        doc: extractDocComment(child),
        exported: true,
        branch: ""
      )
    of nkSym:
      # Symbol reference (shouldn't happen in raw AST, but handle it)
      result.add FieldInfo(
        name: $child,
        typ: "",
        doc: "",
        exported: true,
        branch: ""
      )
    else:
      discard

proc extractProcDoc(n: PNode): string =
  ## Extract doc comment from a proc definition
  ## The doc comment can be on the proc node itself or on the first statement in the body
  result = extractDocComment(n)
  if result.len == 0 and n.len > routineBodyIdx:
    let body = n[routineBodyIdx]
    if body != nil and body.kind == nkStmtList and body.len > 0:
      # Check if first statement has a comment
      result = extractDocComment(body[0])
      if result.len == 0 and body[0].kind == nkCommentStmt:
        result = body[0].comment.strip

proc extractProc(n: PNode, kind: string): DocEntry =
  ## Extract documentation from a proc/func/etc definition
  result.name = extractName(n[routineNameIdx])
  result.kind = kind
  result.line = n.info.line.int
  result.doc = extractProcDoc(n)
  result.exported = isExported(n[routineNameIdx])

  if n.len > routineParamsIdx:
    result.params = extractParams(n[routineParamsIdx])
    result.returns = extractReturnType(n[routineParamsIdx])

  # Extract pragmas at the correct index
  if n.len > routinePragmasIdx and n[routinePragmasIdx].kind == nkPragma:
    result.pragmas = extractPragmas(n[routinePragmasIdx])
    result.raises = extractRaises(n[routinePragmasIdx])

  result.signature = renderSignature(n, kind, result.name)

proc extractType(n: PNode): DocEntry =
  ## Extract documentation from a type definition
  ## nkTypeDef structure: [name, genericParams, typeImpl]
  result.kind = "type"
  result.doc = extractDocComment(n)
  result.line = n.info.line.int
  result.name = extractName(n[0])
  result.exported = isExported(n[0])
  result.fields = @[]
  result.values = @[]

  # Build full signature with type definition (excluding fields for cleaner display)
  var sig = "type " & result.name

  # Add generic params if present (index 1)
  if n.len > 1 and n[1].kind != nkEmpty:
    sig &= $n[1]

  # Analyze type implementation (index 2)
  if n.len > 2 and n[2].kind != nkEmpty:
    let typeImpl = n[2]
    case typeImpl.kind
    of nkObjectTy:
      # object type: [pragmas, inheritance, recList]
      sig &= " = object"
      if typeImpl.len > 2:
        result.fields = extractObjectFields(typeImpl[2])
      # Extract doc from recList if not on type node
      if result.doc.len == 0 and typeImpl.len > 2 and typeImpl[2] != nil:
        result.doc = extractDocComment(typeImpl[2])
    of nkRefTy:
      # ref object: [objectTy]
      if typeImpl.len > 0 and typeImpl[0].kind == nkObjectTy:
        sig &= " = ref object"
        let objTy = typeImpl[0]
        if objTy.len > 2:
          result.fields = extractObjectFields(objTy[2])
        if result.doc.len == 0 and objTy.len > 2 and objTy[2] != nil:
          result.doc = extractDocComment(objTy[2])
      else:
        sig &= " = " & $typeImpl
    of nkEnumTy:
      sig &= " = enum"
      result.values = extractEnumValues(typeImpl)
      # Extract doc from enum type if not on type node
      if result.doc.len == 0:
        result.doc = extractDocComment(typeImpl)
    else:
      sig &= " = " & $typeImpl

  result.signature = sig

proc extractConst(n: PNode): DocEntry =
  ## Extract documentation from a const definition
  ## nkConstDef structure: [name, type, value]
  result.kind = "const"
  result.doc = extractDocComment(n)
  result.line = n.info.line.int
  result.name = extractName(n[0])
  result.exported = isExported(n[0])

  # Build full signature with type and value
  var sig = "const " & result.name

  # Add type if present (index 1)
  if n.len > 1 and n[1].kind != nkEmpty:
    sig &= ": " & $n[1]

  # Add value if present (index 2)
  if n.len > 2 and n[2].kind != nkEmpty:
    sig &= " = " & $n[2]

  result.signature = sig

  # Store return type for consistency
  if n.len > 1 and n[1].kind != nkEmpty:
    result.returns = $n[1]

proc extractVarName(n: PNode): tuple[name: string, exported: bool, pragmas: seq[string]] =
  ## Extract name, export status, and pragmas from a var/let name node
  ## Handles: nkIdent, nkPostfix, nkPragmaExpr
  result.pragmas = @[]

  if n.kind == nkIdent:
    result.name = $n.ident.s
    result.exported = false
  elif n.kind == nkPostfix and n.len >= 2:
    result.name = extractName(n)
    result.exported = true
  elif n.kind == nkPragmaExpr and n.len >= 2:
    # nkPragmaExpr: [name, nkPragma]
    let (innerName, innerExported, _) = extractVarName(n[0])
    result.name = innerName
    result.exported = innerExported
    if n[1].kind == nkPragma:
      result.pragmas = extractPragmas(n[1])
  else:
    result.name = ""
    result.exported = false

proc extractVar(n: PNode, kind: string): DocEntry =
  ## Extract documentation from a var/let definition
  ## nkIdentDefs structure: [name(s), type, value]
  result.kind = kind
  result.doc = extractDocComment(n)
  result.line = n.info.line.int

  # Extract name with potential pragmas
  let (name, exported, pragmas) = extractVarName(n[0])
  result.name = name
  result.exported = exported
  result.pragmas = pragmas

  # Build full signature
  var sig = kind & " " & result.name

  # Add type if present (second to last element)
  if n.len >= 2 and n[^2].kind != nkEmpty:
    sig &= ": " & $n[^2]
    result.returns = $n[^2]

  # Add value if present (last element)
  if n.len >= 1 and n[^1].kind != nkEmpty:
    sig &= " = " & $n[^1]

  result.signature = sig

proc walkAst(n: PNode, entries: var seq[DocEntry]) =
  ## Walk AST and collect documentation entries
  if n == nil:
    return

  case n.kind
  of nkProcDef:
    entries.add extractProc(n, "proc")
  of nkFuncDef:
    entries.add extractProc(n, "func")
  of nkIteratorDef:
    entries.add extractProc(n, "iterator")
  of nkTemplateDef:
    entries.add extractProc(n, "template")
  of nkMacroDef:
    entries.add extractProc(n, "macro")
  of nkTypeDef:
    entries.add extractType(n)
  of nkConstDef:
    entries.add extractConst(n)
  of nkVarSection:
    # var section contains nkIdentDefs
    for child in n:
      if child.kind == nkIdentDefs:
        entries.add extractVar(child, "var")
  of nkLetSection:
    # let section contains nkIdentDefs
    for child in n:
      if child.kind == nkIdentDefs:
        entries.add extractVar(child, "let")
  else:
    for child in n:
      walkAst(child, entries)

proc extractModule*(filepath: string): ModuleDoc =
  ## Extract all documentation from a Nim source file
  result.file = filepath
  result.module = filepath.splitFile.name
  result.entries = @[]

  # Parse the file
  var conf = newConfigRef()
  conf.verbosity = 0

  let fileIdx = fileInfoIdx(conf, AbsoluteFile(filepath))
  var parser: Parser

  let source = readFile(filepath)
  openParser(parser, fileIdx, llStreamOpen(source), newIdentCache(), conf)

  let ast = parseAll(parser)
  closeParser(parser)

  # Extract module doc comment
  if ast.len > 0 and ast[0].comment.len > 0:
    result.doc = ast[0].comment.strip

  walkAst(ast, result.entries)

proc toJson*(doc: ModuleDoc): JsonNode =
  ## Convert module documentation to JSON
  result = %*{
    "module": doc.module,
    "file": doc.file,
    "doc": doc.doc,
    "entries": []
  }

  for entry in doc.entries:
    var entryJson = %*{
      "name": entry.name,
      "kind": entry.kind,
      "line": entry.line,
      "signature": entry.signature,
      "doc": entry.doc,
      "exported": entry.exported
    }

    if entry.params.len > 0:
      entryJson["params"] = %entry.params.mapIt(%*{"name": it.name, "type": it.typ})

    if entry.returns.len > 0:
      entryJson["returns"] = %entry.returns

    if entry.pragmas.len > 0:
      entryJson["pragmas"] = %entry.pragmas

    if entry.raises.len > 0:
      entryJson["raises"] = %entry.raises

    if entry.fields.len > 0:
      entryJson["fields"] = %entry.fields.mapIt(%*{
        "name": it.name,
        "type": it.typ,
        "doc": it.doc,
        "exported": it.exported,
        "branch": it.branch
      })

    if entry.values.len > 0:
      entryJson["values"] = %entry.values.mapIt(%*{
        "name": it.name,
        "type": it.typ,
        "doc": it.doc,
        "exported": it.exported,
        "branch": it.branch
      })

    result["entries"].add entryJson
