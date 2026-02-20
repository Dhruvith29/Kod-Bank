import { GoogleGenerativeAI } from '@google/generative-ai';

// Access your API key as an environment variable or hardcoded
const genAI = new GoogleGenerativeAI('AIzaSyCSsTlJ3jJ9LAQsf2lxQs_pc7304kzSW7c');

async function test() {
    try {
        const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
        const result = await model.generateContent("Explain how AI works");
        console.log(result.response.text());
    } catch (e) {
        console.dir(e, { depth: null });
    }
}
test();
