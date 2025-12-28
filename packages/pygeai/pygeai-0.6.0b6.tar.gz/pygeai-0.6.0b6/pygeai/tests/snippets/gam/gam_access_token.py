"""
Sample script demonstrating the usage of GAMClient to interact with GAM OAuth 2.0 endpoints.

This script shows how to:
1. Obtain an access token using username and password.
2. Fetch user information using the access token.
3. Refresh an access token using a refresh token.
"""

import argparse
import getpass
from pygeai.gam.clients import GAMClient


def main():
    """
    Main function to demonstrate the usage of GAMClient for GAM OAuth 2.0 authentication.
    """
    parser = argparse.ArgumentParser(description="GAM OAuth 2.0 Authentication Script")
    parser.add_argument("--username", "-u", required=True, help="Username for authentication")
    parser.add_argument("--client-id", "--cid", required=True, help="Client ID for the application")
    parser.add_argument("--client-secret", "--cs", required=True, help="Client secret for the application")
    args = parser.parse_args()

    password = getpass.getpass("Enter password for {}: ".format(args.username))

    try:
        gam_client = GAMClient()
    except Exception as e:
        print(f"Error initializing GAMClient: {e}")
        return

    # Step 1: Get Access Token
    print("=== Step 1: Obtaining Access Token ===")
    try:
        access_token_response = gam_client.get_access_token(
            client_id=args.client_id,
            client_secret=args.client_secret,
            username=args.username,
            password=password,
            scope="gam_user_data+gam_user_roles",
            authentication_type_name="local",
            initial_properties={"Id": "Company", "Value": "GeneXus"},
            repository="",
            request_token_type="OAuth"
        )
        print("Access Token Response:")
        print(access_token_response)

        access_token = access_token_response.get("access_token", "")
        refresh_token = access_token_response.get("refresh_token", "")
        if not access_token:
            print("Error: No access token received.")
            return
    except Exception as e:
        print(f"Error obtaining access token: {e}")
        return

    # Step 2: Get User Information
    print("\n=== Step 2: Fetching User Information ===")
    try:
        user_info_response = gam_client.get_user_info(access_token=access_token)
        print("User Info Response:")
        print(user_info_response)
    except Exception as e:
        print(f"Error fetching user information: {e}")
        return

    # Step 3: Refresh Access Token (if refresh_token is available)
    if refresh_token:
        print("\n=== Step 3: Refreshing Access Token ===")
        try:
            refresh_token_response = gam_client.refresh_access_token(
                client_id=args.client_id,
                client_secret=args.client_secret,
                refresh_token=refresh_token
            )
            print("Refresh Token Response:")
            print(refresh_token_response)
        except Exception as e:
            print(f"Error refreshing access token: {e}")
    else:
        print("\n=== Step 3: Skipping Refresh Token (No refresh token available) ===")


if __name__ == "__main__":
    main()