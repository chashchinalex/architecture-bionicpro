const express = require("express");
const { Pool } = require("pg");
const cors = require("cors");
const helmet = require("helmet");
const session = require("express-session");
const Keycloak = require("keycloak-connect");
require("dotenv").config();

const app = express();
const PORT = process.env.PORT || 8000;

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json());

// Session configuration
const memoryStore = new session.MemoryStore();
app.use(
  session({
    secret: process.env.SESSION_SECRET || "your-secret-key",
    resave: false,
    saveUninitialized: false,
    store: memoryStore,
  })
);

// Keycloak configuration
const keycloakConfig = {
  realm: "reports-realm",
  "auth-server-url": "http://keycloak:8080",
  "ssl-required": "external",
  resource: "reports-api",
  "confidential-port": 0,
  "client-secret": "oNwoLQdvJAvRcL89SydqCWCe5ry1jMgq",
  "bearer-only": true,
};

const keycloak = new Keycloak({ store: memoryStore }, keycloakConfig);

// Keycloak middleware
app.use(keycloak.middleware());

// Database connection
const pool = new Pool({
  user: process.env.DB_USER || "reports_user",
  host: process.env.DB_HOST || "localhost",
  database: process.env.DB_NAME || "reports_db",
  password: process.env.DB_PASSWORD || "reports_password",
  port: process.env.DB_PORT || 5434,
});

// Test database connection
pool.on("connect", () => {
  console.log("Connected to PostgreSQL database");
});

pool.on("error", (err) => {
  console.error("Database connection error:", err);
});

// Middleware to extract user info from Keycloak token and find customer_id
const extractUserInfo = async (req, res, next) => {
  if (req.kauth && req.kauth.grant && req.kauth.grant.access_token) {
    const token = req.kauth.grant.access_token;
    const email = token.content.email || token.content.preferred_username;

    try {
      // Find customer_id by email in CRM table
      const result = await pool.query(
        "SELECT customer_id, name FROM crm_customers WHERE email = $1",
        [email]
      );

      if (result.rows.length > 0) {
        req.userInfo = {
          customer_id: result.rows[0].customer_id,
          email: email,
          name: result.rows[0].name,
          roles: token.content.realm_access?.roles || [],
        };
      } else {
        req.userInfo = {
          customer_id: null,
          email: email,
          name: token.content.name || token.content.given_name,
          roles: token.content.realm_access?.roles || [],
        };
      }
    } catch (error) {
      console.error("Error finding customer:", error);
      req.userInfo = {
        customer_id: null,
        email: email,
        name: token.content.name || token.content.given_name,
        roles: token.content.realm_access?.roles || [],
      };
    }
  }
  next();
};

// Routes

// Health check endpoint
app.get("/health", (req, res) => {
  res.json({ status: "OK", timestamp: new Date().toISOString() });
});

// Get user's own report (protected route) - manual token validation
app.get("/reports", async (req, res) => {
  try {
    console.log("Reports endpoint called");

    // Check for Authorization header
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      return res.status(401).json({
        success: false,
        error: "Access denied. No token provided.",
      });
    }

    const token = authHeader.substring(7);
    console.log("Token received:", token.substring(0, 20) + "...");

    // Decode token to get email
    const tokenPayload = JSON.parse(
      Buffer.from(token.split(".")[1], "base64").toString()
    );
    const userEmail = tokenPayload.email || tokenPayload.preferred_username;
    console.log("User email from token:", userEmail);

    // Find customer_id by email
    const customerResult = await pool.query(
      "SELECT customer_id FROM crm_customers WHERE email = $1",
      [userEmail]
    );

    if (customerResult.rows.length === 0) {
      return res.status(404).json({
        success: false,
        error: "Customer not found for this user",
      });
    }

    const customerId = customerResult.rows[0].customer_id;
    console.log("Using customer_id:", customerId);

    const result = await pool.query(
      `
      SELECT 
        report_id,
        customer_id,
        customer_name,
        customer_email,
        prosthesis_type,
        report_date,
        total_sessions,
        avg_muscle_signal,
        max_muscle_signal,
        min_muscle_signal,
        avg_position,
        total_activities,
        most_common_activity,
        created_at
      FROM reports_data_mart
      WHERE customer_id = $1
      ORDER BY created_at DESC
    `,
      [customerId]
    );

    res.json({
      success: true,
      data: result.rows,
      count: result.rows.length,
    });
  } catch (error) {
    console.error("Error fetching reports:", error);
    res.status(500).json({
      success: false,
      error: "Internal server error",
    });
  }
});

// Get report by customer ID (protected route - user can only see their own data)
app.get(
  "/reports/customer/:customerId",
  keycloak.protect(),
  extractUserInfo,
  async (req, res) => {
    try {
      // Check if user has prothetic_user role
      if (!req.userInfo.roles.includes("prothetic_user")) {
        return res.status(403).json({
          success: false,
          error: "Access denied. Prothetic user role required.",
        });
      }

      const { customerId } = req.params;

      // Get customer_id from user info or find by email
      let userCustomerId = req.userInfo.customer_id;

      if (!userCustomerId) {
        // Find customer by email
        const customerResult = await pool.query(
          "SELECT customer_id FROM crm_customers WHERE email = $1",
          [req.userInfo.email]
        );

        if (customerResult.rows.length === 0) {
          return res.status(404).json({
            success: false,
            error: "Customer not found for this user",
          });
        }

        userCustomerId = customerResult.rows[0].customer_id;
      }

      // Check if user is trying to access their own data
      if (parseInt(customerId) !== userCustomerId) {
        return res.status(403).json({
          success: false,
          error: "Access denied. You can only view your own reports.",
        });
      }

      const result = await pool.query(
        `
        SELECT 
          report_id,
          customer_id,
          customer_name,
          customer_email,
          prosthesis_type,
          report_date,
          total_sessions,
          avg_muscle_signal,
          max_muscle_signal,
          min_muscle_signal,
          avg_position,
          total_activities,
          most_common_activity,
          created_at
        FROM reports_data_mart
        WHERE customer_id = $1
        ORDER BY created_at DESC
      `,
        [customerId]
      );

      if (result.rows.length === 0) {
        return res.status(404).json({
          success: false,
          error: "Report not found for this customer",
        });
      }

      res.json({
        success: true,
        data: result.rows[0],
      });
    } catch (error) {
      console.error("Error fetching customer report:", error);
      res.status(500).json({
        success: false,
        error: "Internal server error",
      });
    }
  }
);

// Get detailed telemetry data for a customer (protected route)
app.get(
  "/reports/customer/:customerId/telemetry",
  keycloak.protect(),
  extractUserInfo,
  async (req, res) => {
    try {
      // Check if user has prothetic_user role
      if (!req.userInfo.roles.includes("prothetic_user")) {
        return res.status(403).json({
          success: false,
          error: "Access denied. Prothetic user role required.",
        });
      }

      const { customerId } = req.params;

      // Get customer_id from user info or find by email
      let userCustomerId = req.userInfo.customer_id;

      if (!userCustomerId) {
        // Find customer by email
        const customerResult = await pool.query(
          "SELECT customer_id FROM crm_customers WHERE email = $1",
          [req.userInfo.email]
        );

        if (customerResult.rows.length === 0) {
          return res.status(404).json({
            success: false,
            error: "Customer not found for this user",
          });
        }

        userCustomerId = customerResult.rows[0].customer_id;
      }

      // Check if user is trying to access their own data
      if (parseInt(customerId) !== userCustomerId) {
        return res.status(403).json({
          success: false,
          error: "Access denied. You can only view your own telemetry data.",
        });
      }

      const { limit = 100, offset = 0 } = req.query;

      const result = await pool.query(
        `
        SELECT 
          t.telemetry_id,
          t.customer_id,
          t.timestamp,
          t.device_id,
          t.sensor_type,
          t.value,
          t.unit,
          t.activity_type
        FROM telemetry_data t
        WHERE t.customer_id = $1
        ORDER BY t.timestamp DESC
        LIMIT $2 OFFSET $3
      `,
        [customerId, limit, offset]
      );

      res.json({
        success: true,
        data: result.rows,
        count: result.rows.length,
        pagination: {
          limit: parseInt(limit),
          offset: parseInt(offset),
        },
      });
    } catch (error) {
      console.error("Error fetching telemetry data:", error);
      res.status(500).json({
        success: false,
        error: "Internal server error",
      });
    }
  }
);

// Get customer statistics (protected route)
app.get(
  "/reports/customer/:customerId/stats",
  keycloak.protect(),
  extractUserInfo,
  async (req, res) => {
    try {
      // Check if user has prothetic_user role
      if (!req.userInfo.roles.includes("prothetic_user")) {
        return res.status(403).json({
          success: false,
          error: "Access denied. Prothetic user role required.",
        });
      }

      const { customerId } = req.params;

      // Get customer_id from user info or find by email
      let userCustomerId = req.userInfo.customer_id;

      if (!userCustomerId) {
        // Find customer by email
        const customerResult = await pool.query(
          "SELECT customer_id FROM crm_customers WHERE email = $1",
          [req.userInfo.email]
        );

        if (customerResult.rows.length === 0) {
          return res.status(404).json({
            success: false,
            error: "Customer not found for this user",
          });
        }

        userCustomerId = customerResult.rows[0].customer_id;
      }

      // Check if user is trying to access their own data
      if (parseInt(customerId) !== userCustomerId) {
        return res.status(403).json({
          success: false,
          error: "Access denied. You can only view your own statistics.",
        });
      }

      const result = await pool.query(
        `
        SELECT 
          c.customer_id,
          c.name,
          c.email,
          c.prosthesis_type,
          COUNT(DISTINCT DATE(t.timestamp)) as total_days,
          COUNT(t.telemetry_id) as total_measurements,
          AVG(CASE WHEN t.sensor_type = 'muscle_signal' THEN t.value END) as avg_muscle_signal,
          MAX(CASE WHEN t.sensor_type = 'muscle_signal' THEN t.value END) as max_muscle_signal,
          MIN(CASE WHEN t.sensor_type = 'muscle_signal' THEN t.value END) as min_muscle_signal,
          AVG(CASE WHEN t.sensor_type = 'position' THEN t.value END) as avg_position,
          COUNT(DISTINCT t.activity_type) as unique_activities,
          MODE() WITHIN GROUP (ORDER BY t.activity_type) as most_common_activity
        FROM crm_customers c
        LEFT JOIN telemetry_data t ON c.customer_id = t.customer_id
        WHERE c.customer_id = $1
        GROUP BY c.customer_id, c.name, c.email, c.prosthesis_type
      `,
        [customerId]
      );

      if (result.rows.length === 0) {
        return res.status(404).json({
          success: false,
          error: "Customer not found",
        });
      }

      res.json({
        success: true,
        data: result.rows[0],
      });
    } catch (error) {
      console.error("Error fetching customer stats:", error);
      res.status(500).json({
        success: false,
        error: "Internal server error",
      });
    }
  }
);

// Error handling middleware
app.use((err, req, res, next) => {
  console.error("Unhandled error:", err);
  res.status(500).json({
    success: false,
    error: "Internal server error",
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    success: false,
    error: "Endpoint not found",
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`Reports API server running on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
  console.log(`Reports endpoint: http://localhost:${PORT}/reports`);
  console.log(`Keycloak integration enabled`);
});
