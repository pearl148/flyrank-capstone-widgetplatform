# Design — Embeddable Widget & Lead-Capture Platform

## 1. Problem

Let a customer (tenant) define a widget (signup form, CTA, popover) and embed it
on any external website with a single `<script>` tag. Visitors on that external
site submit the widget's form; submissions must be validated, protected against
abuse, enriched with geo data, stored safely, and made visible to the widget's
owner in a dashboard.

Three actors, three trust levels:
- **Widget Owner** — authenticated, trusted, owns tenant data.
- **Customer Website** — public, no identity, just loads a script.
- **Website Visitor** — public, untrusted, submits a form from anywhere.

## 2. Data model

**Tenant** — the customer account. Kept separate from `User` so isolation logic
and future multi-user-per-tenant support are clean.
```
Tenant
  id            PK
  name
  created_at
```

**User** — the login for a tenant (assume 1 tenant : 1 user for this capstone).
```
User
  id              PK
  tenant_id       FK -> Tenant
  email           unique
  password_hash
  created_at
```

**Widget** — belongs to a tenant.
```
Widget
  id                PK
  tenant_id         FK -> Tenant   (indexed)
  type              enum: signup_form | cta | popover
  title
  description
  fields            JSON   (form field definitions)
  button_text
  display_options   JSON   (colors, position, etc.)
  version           int    (bumped on script-affecting change)
  created_at
```

**Submission** — a visitor's form entry.
```
Submission
  id            PK
  widget_id     FK -> Widget      (indexed)
  tenant_id     FK -> Tenant      (indexed, duplicated from Widget on purpose —
                                   see "Design decisions" below)
  data          JSON   (submitted field values, shape depends on widget.fields)
  ip_address
  country
  city
  status        enum: stored | spam_rejected
  created_at
```

### Indexes
- `Widget.tenant_id`
- `Submission.widget_id`
- `Submission.tenant_id`
- `User.email` (unique)

## 3. Design decisions

- **`tenant_id` is duplicated on `Submission`** even though it's reachable via
  `Submission → Widget → tenant_id`. Two reasons: (1) avoids a join on every
  tenant-scoped submissions query, and (2) makes the tenant-isolation filter a
  flat `WHERE tenant_id = :current_tenant` on every query — structurally harder
  to forget than a join-based filter, which matters a lot for a security
  requirement like tenant isolation.
- **Submitted form data is stored as JSON**, not rigid columns, since different
  widget types/instances define different fields. Validation happens against
  the widget's own `fields` definition at write time, not the DB schema.
- **`Widget.version` exists for cache-busting** the served JS bundle
  (`widget.v1.js`, `widget.v2.js`) — content at a versioned URL never changes,
  so it can be cached forever (`immutable`); new versions get new URLs.

## 4. Request paths / API surface

```
Auth
  POST /login

Widget management (authenticated, tenant-scoped)
  POST   /widgets
  GET    /widgets
  GET    /widgets/{id}
  PUT    /widgets/{id}
  DELETE /widgets/{id}

Widget delivery (public)
  GET /widget.js                 -- static script, long cache, immutable
  GET /widgets/{id}/config       -- per-widget JSON config, short cache (~60s)

Public submission (untrusted input, CORS-enabled)
  POST /submissions

Dashboard (authenticated, tenant-scoped)
  GET /dashboard/submissions     -- list, filterable by widget
  GET /dashboard/stats           -- counts over time, geo breakdown
```

## 5. Embed flow

1. Owner creates a widget via the Widget management API → gets back an
   embed snippet: `<script src=".../widget.js?id={widget_id}"></script>`.
2. Customer pastes the snippet into their site. Browser loads `widget.js`
   (same file for everyone, cached long-term).
3. The script reads `?id=` from its own `<script>` tag, calls
   `GET /widgets/{id}/config` to fetch that widget's title/fields/etc.
4. Script renders the form on the page.
5. Visitor submits → `POST /submissions` (cross-origin, must handle CORS
   preflight, validate input, rate-limit, spam-check, enrich with geo via a
   provider fallback chain, store, then attempt a best-effort side effect
   like a confirmation email).
6. Owner views results via the Dashboard API.

## 6. Non-goal

No real CDN, domain, or hosting. The "customer site" is a plain HTML file
served from a second local port (or `file://`), used purely to prove the
cross-origin request path works. No form-builder UI, no more than 1–2 widget
types implemented.