#!/bin/bash
# setup-keycloak-ad.sh - Automated Keycloak AD User Federation Configuration

# Configuration
KEYCLOAK_URL=${KEYCLOAK_URL:-"http://localhost:8080"}
ADMIN_USER=${ADMIN_USER:-"admin"}
ADMIN_PASSWORD=${ADMIN_PASSWORD:-"admin"}
REALM_NAME=${REALM_NAME:-"enterprise"}

# AD Configuration
AD_DISPLAY_NAME="Active-Directory"
AD_LDAP_URL=${AD_LDAP_URL:-"ldap://ad-server:389"}
AD_USERS_DN=${AD_USERS_DN:-"ou=Users,dc=example,dc=com"}
AD_BIND_DN=${AD_BIND_DN:-"cn=admin,dc=example,dc=com"}
AD_BIND_CREDENTIAL=${AD_BIND_CREDENTIAL:-"password"}

echo "Authenticating with Keycloak..."
TOKEN=$(curl -s -d "client_id=admin-cli" -d "username=$ADMIN_USER" -d "password=$ADMIN_PASSWORD" -d "grant_type=password" "$KEYCLOAK_URL/realms/master/protocol/openid-connect/token" | jq -r .access_token)

if [ "$TOKEN" == "null" ]; then
    echo "Failed to authenticate."
    exit 1
fi

echo "Configuring AD User Federation..."
curl -v -X POST "$KEYCLOAK_URL/admin/realms/$REALM_NAME/components" \
-H "Authorization: Bearer $TOKEN" \
-H "Content-Type: application/json" \
-d '{
    "name": "'"$AD_DISPLAY_NAME"'",
    "providerId": "ldap",
    "providerType": "org.keycloak.storage.UserStorageProvider",
    "parentId": "'"$REALM_NAME"'",
    "config": {
        "enabled": ["true"],
        "priority": ["0"],
        "vendor": ["ad"],
        "connectionUrl": ["'"$AD_LDAP_URL"'"],
        "usersDn": ["'"$AD_USERS_DN"'"],
        "bindDn": ["'"$AD_BIND_DN"'"],
        "bindCredential": ["'"$AD_BIND_CREDENTIAL"'"],
        "useTruststoreSpi": ["always"],
        "connectionTimeout": ["5000"],
        "readTimeout": ["5000"],
        "pagination": ["true"],
        "allowEmptyPassword": ["false"]
    }
}'

echo "Done."
