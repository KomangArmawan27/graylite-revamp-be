-- Proposal: Durable Idempotency Table for Multi-Worker Deployments
CREATE TABLE [System].[Api.Idempotency] (
    [composite_key] VARCHAR(255) NOT NULL PRIMARY KEY,
    [user_id] INT NOT NULL,
    [route] VARCHAR(255) NOT NULL,
    [idempotency_key] VARCHAR(64) NOT NULL,
    [body_hash] VARCHAR(64) NOT NULL,
    [status_code] INT NOT NULL,
    [response_body] VARBINARY(MAX) NOT NULL,
    [created_at] DATETIME2 NOT NULL DEFAULT GETDATE()
);
CREATE INDEX IX_Api_Idempotency_Created ON [System].[Api.Idempotency] ([created_at]);
