from seven2one.questra.authentication import QuestraAuthentication

from seven2one.questra.data import QuestraDataCore

url = "https://dev.questra.s2o.dev/dynamic-objects/graphql"
auth_client = QuestraAuthentication(
    url="https://authentik.dev.questra.s2o.dev", interactive=True
)
core_client = QuestraDataCore(graphql_url=url, auth_client=auth_client)
namespace = "TestDaten"
core_client.mutations.delete_inventory(
    inventory_name="Sensoren", namespace_name=namespace
)
core_client.mutations.delete_inventory(
    inventory_name="Raeume", namespace_name=namespace
)
core_client.mutations.delete_inventory(
    inventory_name="Gebaeude", namespace_name=namespace
)
