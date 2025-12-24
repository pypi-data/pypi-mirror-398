## nimdocinfo - Extract documentation from Nim source files
import std/[json, os]
import extractor

const
  JsonStartMarker* = "<<MKDOCSTRINGS_JSON_START>>"
  JsonEndMarker* = "<<MKDOCSTRINGS_JSON_END>>"

when isMainModule:
  if paramCount() < 1:
    echo "Usage: nimdocinfo <file.nim>"
    quit(1)

  let filepath = paramStr(1)
  if not fileExists(filepath):
    echo "Error: File not found: ", filepath
    quit(1)

  let doc = extractModule(filepath)
  echo JsonStartMarker
  echo doc.toJson.pretty
  echo JsonEndMarker
