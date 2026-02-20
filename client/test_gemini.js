const apiKey = 'AIzaSyDZtwYwGRSoWyzv17_-WaEMQzEcsPR8Xj0';
const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent`;

async function test() {
    const res = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'x-goog-api-key': apiKey
        },
        body: JSON.stringify({
            contents: [{ parts: [{ text: "Hello" }] }]
        })
    });
    const data = await res.json();
    console.log(JSON.stringify(data, null, 2));
}
test();
