
## Prequesites

Make sure you have [bun](https://bun.com/) installed!

You will also need:
- a GitHub account
- a Fly.io account (free, no credit card)

## What you’re learning

### Hono
A tiny web framework- you define routes like, kind of like Express:
- “When someone does `GET /api/stuff`, run this function.”
### SQLite
A database thats just a file (like `my.db`) on your computer, this way things can persist!
### Drizzle
A TypeScript ORM that lets you:
- define your tables in `schema.ts`
- query them with TypeScript instead of raw SQL strings
### drizzle-kit
A CLI tool that takes your schema and creates/updates the real database so you dont have to manually!

---
## Your Project

You’ll end up with your own project that has:

- a working Hono server
- a SQLite file on disk
- Drizzle schema + queries
- a couple API endpoints that read/write the DB

In this workshop ill show you how to set all this up, what you actually make is up to you, it'd be super cool if it was Christmas themed though!

---

# Project structure

This is the layout you're aiming for:

```
beans-cool-api/
  .env
  drizzle.config.ts
  my.db                (created after push)
  src/
    index.ts           (Hono server + routes)
    db/
      schema.ts        (table definitions)
      index.ts         (runtime DB connection)
      queries.ts       (helper functions: list/create/update/delete)
```

---

# Step 1 - Create a Hono project

### 1.1 Create + run

```bash
bun create hono@latest my-project
cd my-project
bun install
bun run dev
```

Your terminal prints a URL. Open it.

### 1.2 Add a route

In `src/index.ts`:

```ts
import { Hono } from "hono"

const app = new Hono()

app.get("/", (c) => c.text("Beans!"))

export default app
```

If you see “Beans!” when your open the url Hono printed, your server works! Yipeeeee

---

# Step 2 - Install Drizzle + tools

```bash
bun add drizzle-orm dotenv
bun add -D drizzle-kit @types/bun
```

What this does:

- `drizzle-orm` = what you use in your code
- `drizzle-kit` = what you run in the terminal
- `dotenv` = loads `.env` file values

---

# Step 3 - Decide where your database file lives

Create `.env` in the project root:

```env
DB_FILE_NAME=./my.db
```

This is the file SQLite will store data in.

Add to `.gitignore`:

```
.env
my.db
```

---

# Step 4 - Define your database schema (the blueprint)

Think of schema as: the database’s "types":

- table name
- column names
- column types
- default values
### Example schema

Create `src/db/schema.ts`:

```ts
import { sqliteTable, integer, text } from "drizzle-orm/sqlite-core"

export const wishes = sqliteTable("wishes", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  item: text("item").notNull(),
  fulfilled: integer("fulfilled").notNull().default(0),
  createdAt: integer("created_at").notNull(),
})
```

Your table could be `quests`, `scores`, `cookies`, `notes`… anything.

You only need:
- one table to start
- a primary key id is needed per table
- a couple fields you care about

Its up to you what you put in it, below is a cheat sheet!

**Primary key (your table needs this, it needs to be unique)**

```ts
id: integer("id").primaryKey({ autoIncrement: true }),
```

**Text / strings**

```ts
text("name").notNull()     // required because of notNull
text("notes")             // optional text
```

**Numbers / booleans**

```ts
integer("count").notNull()
integer("done").notNull().default(0)  // 0 = false, 1 = true SQLite doesnt have real booleans
```


---

# Step 5 - Tell drizzle-kit where your schema is

Create `drizzle.config.ts` in project root:

```ts
import "dotenv/config"
import { defineConfig } from "drizzle-kit"

export default defineConfig({
  out: "./drizzle",
  schema: "./src/db/schema.ts",
  dialect: "sqlite",
  dbCredentials: {
    url: process.env.DB_FILE_NAME!,
  },
})
```

---

# Step 6 - Create/update the DB file from your schema

Run:

```bash
bunx drizzle-kit push
```

After this:
- your `my.db` file should exist
- your table should exist inside it

If you change your schema later (add a column), run `push` again.

---

# Step 7 - Connect your running server to the DB

This is the part that makes routes actually talk to the database.

Create `src/db/index.ts`:

```ts
import "dotenv/config"
import { drizzle } from "drizzle-orm/bun-sqlite"

export const db = drizzle(process.env.DB_FILE_NAME!)
```

Now the server can use `db` to query your SQLite file.

---

# Step 8 - Put DB code in helper functions

Routes should be readable. So we make helper functions like:

- `listThings()`
- `createThing()`
- `updateThing()`
- `deleteThing()`

### Example helpers

Create `src/db/queries.ts`:

```ts
import { db } from "./index"
import { wishes } from "./schema"
import { eq, desc } from "drizzle-orm"

export function listWishes() {
  return db.select().from(wishes).orderBy(desc(wishes.id)).all()
}

export function createWish(item: string) {
  const createdAt = Math.floor(Date.now() / 1000)

  const res = db.insert(wishes).values({
    item,
    fulfilled: 0,
    createdAt,
  }).run()

  return { id: Number(res.lastInsertRowid) }
}

export function fulfillWish(id: number) {
  const res = db.update(wishes)
    .set({ fulfilled: 1 })
    .where(eq(wishes.id, id))
    .run()

  return { changes: res.changes }
}

export function deleteWish(id: number) {
  const res = db.delete(wishes).where(eq(wishes.id, id)).run()
  return { changes: res.changes }
}
```

Again: **this is an example, do whatever you want!**

---

# Step 9 - Write API routes that use those helpers

Now your routes become short and understandable.

### Example API routes

In `src/index.ts`:

```ts
import { createWish, deleteWish, fulfillWish, listWishes } from "./db/queries"

app.get("/api/wishes", (c) => c.json(listWishes()))

app.post("/api/wishes", async (c) => {
  const body = await c.req.json().catch(() => null)
  const item = (body?.item ?? "").toString().trim()
  if (!item) return c.json({ error: "item is required" }, 400)

  return c.json(createWish(item), 201)
})

app.patch("/api/wishes/:id/fulfill", (c) => {
  const id = Number(c.req.param("id"))
  if (!Number.isFinite(id)) return c.json({ error: "bad id" }, 400)

  const res = fulfillWish(id)
  if (res.changes === 0) return c.json({ error: "not found" }, 404)

  return c.json({ ok: true })
})

app.delete("/api/wishes/:id", (c) => {
  const id = Number(c.req.param("id"))
  if (!Number.isFinite(id)) return c.json({ error: "bad id" }, 400)

  const res = deleteWish(id)
  if (res.changes === 0) return c.json({ error: "not found" }, 404)

  return c.json({ ok: true })
})
```

That’s the pattern you can reuse forever:
- validate
- call helper
- return JSON
---
# Step 10 - Test it

This is an **example** of how u can text your APIs!

Add a wish:

```bash
curl -X POST http://localhost:8181/api/wishes \
  -H "content-type: application/json" \
  -d '{"item":"lego"}'
```

List:

```bash
curl http://localhost:8181/api/wishes
```

Fulfill:

```bash
curl -X PATCH http://localhost:8181/api/wishes/1/fulfill
```

Delete:

```bash
curl -X DELETE http://localhost:8181/api/wishes/1
```

---

# Now it’s YOUR PROJECT time!

You now have the entire pipeline:
1. define schema
2. push schema to DB
3. connect DB in runtime
4. write queries
5. write routes
# Step 11 - Make the server deployable

Hosting providers set the port for you.  
You **must** read `process.env.PORT`.

At the bottom of `src/index.ts`, replace the export with:

```ts
const port = Number(process.env.PORT) || 3000

export default {
  port,
  fetch: app.fetch,
}
```

Local dev still works. Deployment will now work too.

---

# Step 12 - Deploy to FastDeploy (custom)

```bash
bunx drizzle-kit push
bun install -g fastdeploy-hono
fastdeploy login 
fastdeploy
```

---
# Step 13 - Push to GitHub

### 14.1 Init git

```bash
git init
git add .
git commit -m "initial hono + drizzle + sqlite api"
```

---

### 14.2 Create GitHub repo

- New repo on GitHub
- Do not add README or .gitignore

---

### 14.3 Push

```bash
git branch -M main
git remote add origin https://github.com/YOURNAME/beans-cool-api.git
git push -u origin main
```

Once you are done making your own project, [https://forms.hackclub.com/haxmas-day-4](https://forms.hackclub.com/haxmas-day-4) your project! Have fun!
