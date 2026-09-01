# Authentication and Authorization

## Overview

Proto applications must use secure authentication and authorization mechanisms to protect user accounts, internal systems, and company data.

## Authentication

Authentication verifies the identity of a user or service.

Applications may use:

* Email and password authentication
* OAuth-based authentication
* Single Sign-On (SSO)
* Secure service-to-service authentication

Passwords must never be stored as plain text. Passwords must be securely hashed using an approved password hashing algorithm.

## Authorization

Authorization determines what an authenticated user is allowed to access.

Applications should implement role-based access control where appropriate.

Example roles include:

* Admin
* Manager
* Employee
* Viewer

Users should only have access to resources required for their responsibilities.

## Tokens and Sessions

Authentication tokens must have appropriate expiration periods. Sensitive tokens must not be exposed through logs, URLs, frontend source code, or public repositories.

Refresh tokens and session credentials must be stored securely.

## Secrets

API keys, passwords, database credentials, private tokens, and other secrets must never be committed to Git repositories.

Secrets should be stored using environment variables or an approved secrets-management system.

## Security Requirements

* Use HTTPS for production communication.
* Validate authentication tokens on protected endpoints.
* Apply authorization checks before accessing protected resources.
* Implement rate limiting where required.
* Log security events without logging passwords or authentication tokens.
* Immediately revoke compromised credentials.

## Access Reviews

Access permissions should be reviewed periodically. Employees who change roles or leave Proto must have unnecessary access removed promptly.
