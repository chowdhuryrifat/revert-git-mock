DO $$ BEGIN
  CREATE TYPE channel_type AS ENUM ('app', 'sms', 'call_center', 'merchant_portal');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE locale_type AS ENUM ('bn', 'en', 'mixed');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE case_type AS ENUM ('wrong_transfer', 'payment_failed', 'refund_request', 'phishing_or_social_engineering', 'other');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE severity_level AS ENUM ('low', 'medium', 'high', 'critical');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE department_type AS ENUM ('customer_support', 'dispute_resolution', 'payments_ops', 'fraud_risk');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE ticket_requests (
    id            BIGSERIAL,
    ticket_id     TEXT        NOT NULL,
    channel       channel_type,
    locale        locale_type,
    message       TEXT        NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);


CREATE TABLE ticket_requests_2026_01 PARTITION OF ticket_requests
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
CREATE TABLE ticket_requests_2026_02 PARTITION OF ticket_requests
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
CREATE TABLE ticket_requests_2026_03 PARTITION OF ticket_requests
    FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');
CREATE TABLE ticket_requests_2026_04 PARTITION OF ticket_requests
    FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');
CREATE TABLE ticket_requests_2026_05 PARTITION OF ticket_requests
    FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');
CREATE TABLE ticket_requests_2026_06 PARTITION OF ticket_requests
    FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');
CREATE TABLE ticket_requests_2026_07 PARTITION OF ticket_requests
    FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');
CREATE TABLE ticket_requests_2026_08 PARTITION OF ticket_requests
    FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');
CREATE TABLE ticket_requests_2026_09 PARTITION OF ticket_requests
    FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');
CREATE TABLE ticket_requests_2026_10 PARTITION OF ticket_requests
    FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');
CREATE TABLE ticket_requests_2026_11 PARTITION OF ticket_requests
    FOR VALUES FROM ('2026-11-01') TO ('2026-12-01');
CREATE TABLE ticket_requests_2026_12 PARTITION OF ticket_requests
    FOR VALUES FROM ('2026-12-01') TO ('2027-01-01');

CREATE TABLE ticket_requests_default PARTITION OF ticket_requests DEFAULT;

CREATE TABLE ticket_responses (
    id                      BIGSERIAL,
    ticket_request_id       BIGINT        NOT NULL,
    ticket_id               TEXT          NOT NULL,
    case_type               case_type     NOT NULL,
    severity                severity_level NOT NULL,
    department              department_type NOT NULL,
    agent_summary           TEXT          NOT NULL,
    human_review_required   BOOLEAN       NOT NULL DEFAULT false,
    confidence              NUMERIC(4,3)  NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    created_at              TIMESTAMPTZ   NOT NULL DEFAULT now(),

    PRIMARY KEY (id, case_type)
) PARTITION BY LIST (case_type);

CREATE TABLE ticket_responses_wrong_transfer PARTITION OF ticket_responses
    FOR VALUES IN ('wrong_transfer');
CREATE TABLE ticket_responses_payment_failed PARTITION OF ticket_responses
    FOR VALUES IN ('payment_failed');
CREATE TABLE ticket_responses_refund_request PARTITION OF ticket_responses
    FOR VALUES IN ('refund_request');
CREATE TABLE ticket_responses_phishing PARTITION OF ticket_responses
    FOR VALUES IN ('phishing_or_social_engineering');
CREATE TABLE ticket_responses_other PARTITION OF ticket_responses
    FOR VALUES IN ('other');

CREATE INDEX idx_ticket_requests_ticket_id    ON ticket_requests (ticket_id);
CREATE INDEX idx_ticket_requests_created_at   ON ticket_requests (created_at);
CREATE INDEX idx_ticket_responses_ticket_id   ON ticket_responses (ticket_id);
CREATE INDEX idx_ticket_responses_severity    ON ticket_responses (severity);
CREATE INDEX idx_ticket_responses_human_review ON ticket_responses (human_review_required) WHERE human_review_required = true;

CREATE INDEX idx_ticket_responses_request_id  ON ticket_responses (ticket_request_id);

ALTER TABLE ticket_requests  ENABLE ROW LEVEL SECURITY;
ALTER TABLE ticket_responses ENABLE ROW LEVEL SECURITY;


CREATE POLICY anon_insert_requests ON ticket_requests
    FOR INSERT TO anon
    WITH CHECK (true);

CREATE POLICY anon_select_requests ON ticket_requests
    FOR SELECT TO anon
    USING (true);

CREATE POLICY anon_insert_responses ON ticket_responses
    FOR INSERT TO anon
    WITH CHECK (true);

CREATE POLICY anon_select_responses ON ticket_responses
    FOR SELECT TO anon
    USING (true);


INSERT INTO ticket_requests (ticket_id, channel, locale, message, created_at)
VALUES
    ('T-001', 'app', 'en', 'I sent 3000 to wrong number',                              '2026-06-25 10:00:00+00'),
    ('T-002', 'app', 'bn', 'Payment failed but balance deducted',                      '2026-06-25 10:01:00+00'),
    ('T-003', 'sms', 'en', 'Someone called asking my OTP, is that bKash?',            '2026-06-25 10:02:00+00'),
    ('T-004', 'app', 'en', 'Please refund my last transaction, I changed my mind',      '2026-06-25 10:03:00+00'),
    ('T-005', 'app', 'en', 'App crashed when I opened it',                             '2026-06-25 10:04:00+00');

INSERT INTO ticket_responses (ticket_request_id, ticket_id, case_type, severity, department, agent_summary, human_review_required, confidence)
VALUES
    (1, 'T-001', 'wrong_transfer',                'high',    'dispute_resolution', 'Customer reports sending 3000 BDT to a wrong number.',                                 true,  0.92),
    (2, 'T-002', 'payment_failed',                'high',    'payments_ops',       'Customer reports payment failed but balance was deducted.',                            true,  0.88),
    (3, 'T-003', 'phishing_or_social_engineering', 'critical', 'fraud_risk',        'Customer reports a suspicious call asking for OTP.',                                      true,  0.95),
    (4, 'T-004', 'refund_request',                'low',     'customer_support',   'Customer requests a refund for the last transaction.',                                  false, 0.80),
    (5, 'T-005', 'other',                         'low',     'customer_support',   'Customer reports the app crashing on open.',                                            false, 0.75);
