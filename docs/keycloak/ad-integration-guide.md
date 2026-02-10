# Keycloak & Active Directory (AD) Integration Guide

This guide describes how to integrate Keycloak with Active Directory / LDAP for User Federation.

## 1. Prerequisites
- A running Keycloak instance.
- Access to an Active Directory (AD) or LDAP server.
- Bind DN and password for the LDAP server.

## 2. Setting up User Federation

1. Log in to the Keycloak Admin Console.
2. Select your Realm (or use `master`).
3. Navigate to **User Federation**.
4. Click **Add provider** and select **ldap**.
5. Configure the following settings:
   - **Edit Mode**: `READ_ONLY` (standard for AD) or `WRITABLE` (if you want Keycloak to update AD).
   - **Vendor**: `Active Directory`.
   - **Username LDAP attribute**: `sAMAccountName`.
   - **RDN LDAP attribute**: `cn`.
   - **UUID LDAP attribute**: `objectGUID`.
   - **User Object Classes**: `person, organizationalPerson, user`.
   - **Connection URL**: `ldap://your-ad-server:389`.
   - **Users DN**: `OU=Users,DC=example,DC=com`.
   - **Bind DN**: `CN=Keycloak Bind,OU=ServiceAccounts,DC=example,DC=com`.
   - **Bind Credential**: `your-bind-password`.

## 3. Attribute Mapping

To ensure the user's name and email are correctly imported:

1. In the LDAP provider configuration, go to the **Mappers** tab.
2. Click **Add mapper**.
3. **Email Mapper**:
   - Name: `email`
   - Mapper Type: `user-attribute-ldap-mapper`
   - User Model Attribute: `email`
   - LDAP Attribute: `mail`
4. **Full Name Mapper**:
   - Name: `full name`
   - Mapper Type: `full-name-ldap-mapper`
   - LDAP Full Name Attribute: `displayName` (or combined `givenName` and `sn`)
5. **First Name Mapper**:
   - Name: `first name`
   - Mapper Type: `user-attribute-ldap-mapper`
   - User Model Attribute: `firstName`
   - LDAP Attribute: `givenName`
6. **Last Name Mapper**:
   - Name: `last name`
   - Mapper Type: `user-attribute-ldap-mapper`
   - User Model Attribute: `lastName`
   - LDAP Attribute: `sn`

## 4. Verifying Login

1. Go to the **Users** section in Keycloak.
2. Click **View all users**. AD users should start appearing (if Sync is enabled or on-demand).
3. Try logging into the Keycloak Account Console (`/realms/{realm}/account`) using an AD user's credentials.
4. Check the **User Details** to ensure email and names are correctly mapped.

## 5. Automation (Optional)

A sample script `setup-keycloak-ad.sh` is provided to demonstrate how to use the Keycloak Admin CLI (`kcadm.sh`) to automate this configuration.
