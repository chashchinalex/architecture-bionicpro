#!/bin/bash

echo "🔐 Setting up Keycloak via API..."

# Wait for Keycloak to be ready
echo "⏳ Waiting for Keycloak to be ready..."
until curl -s http://localhost:8080/realms/master > /dev/null; do
  echo "   Waiting for Keycloak..."
  sleep 5
done

echo "✅ Keycloak is ready!"

# Get admin token
echo "🔑 Getting admin token..."
ADMIN_TOKEN=$(curl -s -X POST http://localhost:8080/realms/master/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" \
  -d "username=admin" \
  -d "password=admin" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$ADMIN_TOKEN" ]; then
  echo "❌ Failed to get admin token"
  exit 1
fi

echo "✅ Admin token obtained"

# Get realm info
REALM_NAME="reports-realm"
echo "📋 Checking realm: $REALM_NAME"

# Check if realm exists
REALM_EXISTS=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8080/admin/realms/$REALM_NAME | grep -o '"realm":"[^"]*"' | cut -d'"' -f4)

if [ -z "$REALM_EXISTS" ]; then
  echo "❌ Realm $REALM_NAME not found"
  echo "   Please create the realm manually or import from realm-export.json"
  exit 1
fi

echo "✅ Realm $REALM_NAME exists"

# Get prothetic_user role
echo "👤 Checking prothetic_user role..."
ROLE_EXISTS=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8080/admin/realms/$REALM_NAME/roles/prothetic_user | grep -o '"name":"[^"]*"' | cut -d'"' -f4)

if [ -z "$ROLE_EXISTS" ]; then
  echo "❌ Role prothetic_user not found"
  echo "   Please create the role manually"
  exit 1
fi

echo "✅ Role prothetic_user exists"

# Function to create user
create_user() {
  local email=$1
  local username=$2
  local firstname=$3
  local lastname=$4
  
  echo "👤 Creating user: $email"
  
  # Check if user exists
  USER_EXISTS=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
    "http://localhost:8080/admin/realms/$REALM_NAME/users?email=$email" | grep -o '"id":"[^"]*"')
  
  if [ ! -z "$USER_EXISTS" ]; then
    echo "   User $email already exists, skipping..."
    return
  fi
  
  # Create user
  USER_DATA='{
    "username": "'$username'",
    "email": "'$email'",
    "firstName": "'$firstname'",
    "lastName": "'$lastname'",
    "enabled": true,
    "emailVerified": true
  }'
  
  USER_RESPONSE=$(curl -s -X POST \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$USER_DATA" \
    http://localhost:8080/admin/realms/$REALM_NAME/users)
  
  if [ $? -eq 0 ]; then
    echo "   ✅ User $email created"
    
    # Get user ID
    USER_ID=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
      "http://localhost:8080/admin/realms/$REALM_NAME/users?email=$email" | grep -o '"id":"[^"]*"' | cut -d'"' -f4 | head -1)
    
    if [ ! -z "$USER_ID" ]; then
      # Set password
      PASSWORD_DATA='{
        "type": "password",
        "value": "password123",
        "temporary": false
      }'
      
      curl -s -X PUT \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$PASSWORD_DATA" \
        http://localhost:8080/admin/realms/$REALM_NAME/users/$USER_ID/reset-password
      
      # Assign prothetic_user role
      ROLE_DATA='[{
        "id": "'$USER_ID'",
        "name": "prothetic_user"
      }]'
      
      curl -s -X POST \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$ROLE_DATA" \
        http://localhost:8080/admin/realms/$REALM_NAME/users/$USER_ID/role-mappings/realm
      
      echo "   ✅ Password set and role assigned for $email"
    fi
  else
    echo "   ❌ Failed to create user $email"
  fi
}

# Create users
echo "👥 Creating users..."
create_user "ivan.petrov@email.com" "ivan.petrov" "Иван" "Петров"
create_user "maria.sidorova@email.com" "maria.sidorova" "Мария" "Сидорова"
create_user "alexey.kozlov@email.com" "alexey.kozlov" "Алексей" "Козлов"
create_user "elena.volkova@email.com" "elena.volkova" "Елена" "Волкова"
create_user "dmitry.novikov@email.com" "dmitry.novikov" "Дмитрий" "Новиков"

echo ""
echo "🎉 Keycloak setup complete!"
echo ""
echo "📋 Test users created:"
echo "   - ivan.petrov@email.com / password123"
echo "   - maria.sidorova@email.com / password123"
echo "   - alexey.kozlov@email.com / password123"
echo "   - elena.volkova@email.com / password123"
echo "   - dmitry.novikov@email.com / password123"
echo ""
echo "🔐 All users have prothetic_user role and can access reports"
