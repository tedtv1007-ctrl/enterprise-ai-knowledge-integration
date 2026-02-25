#!/bin/bash

# Keycloak Admin CLI Configuration Script for AD Integration
# Usage: ./setup-keycloak-ad.sh <KEYCLOAK_URL> <ADMIN_USER> <ADMIN_PASSWORD> <REALM>

KEYCLOAK_URL=$1
ADMIN_USER=$2
ADMIN_PASSWORD=$3
REALM=$4

KC_ADM="/opt/keycloak/bin/kcadm.sh"

# 1. Login to Keycloak
$KC_ADM config credentials --server "$KEYCLOAK_URL" --realm master --user "$ADMIN_USER" --password "$ADMIN_PASSWORD"

# 2. Create LDAP User Federation Provider
PROVIDER_ID=$($KC_ADM create components -r "$REALM" -s name=ad-federation -s providerId=ldap -s providerType=org.keycloak.storage.UserStorageProvider -s 'config={"vendor":["ad"],"connectionUrl":["ldap://ad.example.com:389"],"usersDn":["OU=Users,DC=example,DC=com"],"bindDn":["CN=Keycloak,CN=Users,DC=example,DC=com"],"bindCredential":["password"],"editMode":["READ_ONLY"],"usernameLDAPAttribute":["sAMAccountName"],"rdnLDAPAttribute":["cn"],"uuidLDAPAttribute":["objectGUID"],"userObjectClasses":["person, organizationalPerson, user"]}' --id)

echo "Created LDAP Provider with ID: $PROVIDER_ID"

# 3. Create Mappers
# Email Mapper
$KC_ADM create components -r "$REALM" -s name=email -s providerId=user-attribute-ldap-mapper -s providerType=org.keycloak.storage.ldap.mappers.LDAPStorageMapper -s parentId="$PROVIDER_ID" -s 'config={"user.model.attribute":["email"],"ldap.attribute":["mail"],"read.only":["true"],"always.read.value.from.ldap":["false"],"is.mandatory.in.ldap":["false"]}'

# First Name Mapper
$KC_ADM create components -r "$REALM" -s name="first name" -s providerId=user-attribute-ldap-mapper -s providerType=org.keycloak.storage.ldap.mappers.LDAPStorageMapper -s parentId="$PROVIDER_ID" -s 'config={"user.model.attribute":["firstName"],"ldap.attribute":["givenName"],"read.only":["true"],"always.read.value.from.ldap":["false"],"is.mandatory.in.ldap":["false"]}'

# Last Name Mapper
$KC_ADM create components -r "$REALM" -s name="last name" -s providerId=user-attribute-ldap-mapper -s providerType=org.keycloak.storage.ldap.mappers.LDAPStorageMapper -s parentId="$PROVIDER_ID" -s 'config={"user.model.attribute":["lastName"],"ldap.attribute":["sn"],"read.only":["true"],"always.read.value.from.ldap":["false"],"is.mandatory.in.ldap":["false"]}'

echo "Configuration Complete."
