import click
import requests as _requests
from . import eps_generator


def get_access_token(url, client_id, client_secret):
    response = _requests.post(
        url,
        data={"grant_type": "client_credentials"},
        auth=(client_id, client_secret),
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Error retrieving access token: {response.status_code} - {response.text}")


CONTEXT_SETTINGS = dict(
    help_option_names=['--help'],
    terminal_width=97,
    max_content_width=97,
    color=True,
)
CMD_SETTINGS = dict(
    ignore_unknown_options=True,
    allow_extra_args=True,
)


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option("-n", "--plugin_name", default=None, required=False, help="Plugin name")
@click.option("-o", "--output_dir", default=None, required=False, help="Directory path where to generate whl file")
@click.option("-a", "--http_address", required=True, help="Address of the onetick server")
@click.option("-u", "--http_username", default=None, required=False, help="Username for an http authentication if needed")
@click.option("-p", "--http_password", default=None, required=False, help="Password for an http authentication if needed")
@click.option("-i", "--client_id", default=None, required=False, help="Client id of a user")
@click.option("-s", "--client_secret", default=None, required=False, help="Client secret of a user")
@click.option("-ur", "--url", default=None, required=False, help="Identity provider url")
@click.option("-n", "--namespace", default=None, required=False, help="Namespace names of EPs to generate python code for")
@click.option("-d", "--generate_documentation", default=True, required=False, help="If thue then we also generate the documentation for EPs")
def console(plugin_name, output_dir, http_address, http_username, http_password, client_id, client_secret, url, namespace, generate_documentation):
    if plugin_name:
        if not output_dir:
            raise Exception('output_dir must be specified, when plugin_name is specified')
        if not namespace:
            raise Exception('namespace must be specified, when plugin_name is specified')
    else:
        output_dir = None
        namespace = None
    if not http_address:
        raise Exception('http_address not specified')

    print("EPs generation started")
    if plugin_name:
        print(f"Creating a plugin for {namespace} namespace EPs. Plugin name is {plugin_name}")
    else:
        print("Regenerating all EPs")
    if client_id and client_secret and url:
        access_token = get_access_token(url, client_id, client_secret)
    elif not client_id and not client_secret and not url:
        access_token = None
    else:
        raise Exception('One of url, client_id, client_secret is not specified. '
                        'These parameters must all be specified or none of them should be specified')
    eps_generator.generate_plugin(plugin_name=plugin_name,
                                  output_dir=output_dir,
                                  http_address=http_address,
                                  http_username=http_username,
                                  http_password=http_password,
                                  access_token=access_token,
                                  generate_documentation=generate_documentation,
                                  namespace=namespace)
    print("Done")


if __name__ == '__main__':
    console()
