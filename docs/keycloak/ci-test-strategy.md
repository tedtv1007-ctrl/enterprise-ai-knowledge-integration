# Keycloak and AD Integration CI Test Strategy

## Goal
Verify Keycloak's ability to connect to an LDAP (mocking AD) provider and correctly map user attributes (Email, Display Name, groups).

## Components
1. **Mock LDAP Server**: Using `osixia/openldap` Docker image.
2. **Keycloak Server**: Using `quay.io/keycloak/keycloak` Docker image.
3. **Integration Test Script**: A bash script (`tests/keycloak-ad-test.sh`) that:
    - Waits for Keycloak and LDAP to be ready.
    - Runs `docs/keycloak/setup-keycloak-ad.sh` to configure the connection.
    - Creates a test user in LDAP.
    - Triggers a user sync in Keycloak.
    - Verifies user attributes via Keycloak Admin API.

## Mock LDAP Data
We'll seed the LDAP server with a `testuser` having:
- `cn`: Test User
- `mail`: testuser@example.com
- `memberOf`: cn=Admins,ou=Groups,dc=example,dc=com
