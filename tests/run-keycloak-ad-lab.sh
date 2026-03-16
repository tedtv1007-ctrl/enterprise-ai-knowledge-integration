#!/bin/bash
# run-keycloak-ad-lab.sh - Start Mock AD/Keycloak and run configuration

BASE_DIR=$(dirname "$0")
cd "$BASE_DIR"

echo "🚀 Starting Mock AD (OpenLDAP) and Keycloak..."
docker-compose up -d

# Wait for Keycloak to be healthy
echo "⏳ Waiting for Keycloak to start (8080)..."
until curl -s http://localhost:8080/health/live > /dev/null; do
    sleep 5
    echo -n "."
done
echo "Ready!"

# Seed LDAP data
echo "🌱 Seeding LDAP with test user..."
docker exec -i openldap-server ldapadd -x -D "cn=admin,dc=example,dc=com" -w adminpassword < ldap_seed.ldif

# Run setup script
echo "⚙️ Running Keycloak AD configuration script..."
export KEYCLOAK_URL="http://localhost:8080"
export AD_LDAP_URL="ldap://openldap:389"
export AD_USERS_DN="ou=Users,dc=example,dc=com"
export AD_BIND_DN="cn=admin,dc=example,dc=com"
export AD_BIND_CREDENTIAL="adminpassword"

../docs/keycloak/setup-keycloak-ad.sh

echo "✅ Lab environment is ready."
echo "Keycloak: http://localhost:8080 (admin/admin)"
echo "Test User: ted_tester / password123"
