import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { MongoClient } from 'mongodb';
import { z } from 'zod';

const STORED_NAME = /^[0-9a-f]{24}\.(png|jpg|webp)$/;

const client = new MongoClient(process.env.MONGO_URL ?? 'mongodb://localhost:27017/warhammer', {
    serverSelectionTimeoutMS: 3000,
});
const db = client.db();

async function collectReferences() {
    const [planets, legions, events] = await Promise.all([
        db.collection('planets').find({}, { projection: { name: 1, pic: 1 } }).toArray(),
        db.collection('legions').find({}, { projection: { name: 1, icon: 1 } }).toArray(),
        db.collection('events').find({}, { projection: { name: 1, shots: 1 } }).toArray(),
    ]);
    const owners = new Map();
    const link = (stored, owner) => {
        if (!stored) return;
        owners.set(stored, [...(owners.get(stored) ?? []), owner]);
    };
    planets.forEach((p) => link(p.pic, `planets/${p._id} (${p.name}).pic`));
    legions.forEach((l) => link(l.icon, `legions/${l._id} (${l.name}).icon`));
    events.forEach((e) => (e.shots ?? []).forEach((s) => link(s, `events/${e._id} (${e.name}).shots`)));
    return owners;
}

async function storedFiles() {
    const files = await db.collection('images.files').find({}, { projection: { filename: 1, length: 1, uploadDate: 1 } }).toArray();
    return new Map(files.map((f) => [f.filename, { id: String(f._id), bytes: f.length, uploaded: f.uploadDate }]));
}

function reply(payload, isError = false) {
    return { content: [{ type: 'text', text: JSON.stringify(payload, null, 2) }], isError };
}

const server = new McpServer({ name: 'image-refs', version: '1.0.0' });

server.registerTool(
    'image_refs',
    {
        title: 'GridFS image references',
        description:
            'Read-only. Without arguments: lists GridFS files in bucket "images" that no planet/legion/event references (orphans) ' +
            'and references that point to a missing file (dangling). With `name` (`<objectId>.<png|jpg|webp>`): shows who uses that file and whether it exists.',
        inputSchema: { name: z.string().optional() },
        annotations: { readOnlyHint: true },
    },
    async ({ name }) => {
        if (name !== undefined && !STORED_NAME.test(name)) {
            return reply({ error: `"${name}" is not a stored image name. Expected <24 hex objectId>.<png|jpg|webp>, e.g. 66f1c0ffee0000000000abcd.png` }, true);
        }
        try {
            await client.connect();
            const [owners, files] = await Promise.all([collectReferences(), storedFiles()]);
            if (name) {
                return reply({ name, exists: files.has(name), file: files.get(name) ?? null, referencedBy: owners.get(name) ?? [] });
            }
            const orphans = [...files].filter(([n]) => !owners.has(n)).map(([n, f]) => ({ name: n, ...f }));
            const dangling = [...owners].filter(([n]) => !files.has(n)).map(([n, by]) => ({ name: n, referencedBy: by }));
            return reply({ files: files.size, references: owners.size, orphans, dangling });
        } catch (error) {
            return reply({ error: `MongoDB unavailable: ${error.message}` }, true);
        }
    },
);

await server.connect(new StdioServerTransport());
