from typer.testing import CliRunner

from kurra.cli import app
from kurra.cli.console import console

runner = CliRunner()

# g = Graph().parse(
#     data="""
#     [
#       {
#         "@context": {
#           "olis": "https://olis.dev/",
#           "RealGraph": "olis:RealGraph",
#           "VirtualGraph": "olis:VirtualGraph",
#           "hasGraphRole": "olis:hasGraphRole",
#           "isAliasFor": "olis:isAliasFor",
#           "gr": "https://olis.dev/GraphRoles/"
#         },
#         "@graph": {
#           "@id": "https://example.org/library",
#           "@type": "RealGraph",
#           "hasGraphRole": {"@id": "gr:Original"}
#         }
#       }
#     ]
#     """,
#     format="json-ld",
# )
#
# g.bind("olis", "https://olis.dev/")
# g.bind("gr", "https://olis.dev/GraphRoles/")
#
# print(g.serialize(format="longturtle"))

result = runner.invoke(
    app,
    [
        "shacl",
        "syncv",
    ],
)
# print(result.output)
#
# print("xxxxxx")

# result = runner.invoke(
#     app,
#     [
#         "shacl",
#         "listv",
#     ],
# )


# from kurra.shacl import list_local_validators
#
# print(list_local_validators())

# print(sync_validators())

# result = runner.invoke(
#     app,
#     [
#         "shacl",
#         "validate",
#         str(Path(__file__).parent / "tests/test_shacl/vocab-invalid.ttl"),
#         "8"
#     ],
# )

if result.exception:
    console.print(result.exception)
else:
    console.print(result.output)

# print(validate(Path(__file__).parent / "tests/test_shacl/vocab-valid.ttl", 8))
