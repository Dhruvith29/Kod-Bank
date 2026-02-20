const apiKey = 'AIzaSyCSsTlJ3jJ9LAQsf2lxQs_pc7304kzSW7c';
const url = `https://generativelanguage.googleapis.com/v1beta/models?key=${apiKey}`;

async function test() {
    try {
        const res = await fetch(url);
        const data = await res.json();
        const models = data.models ? data.models.map(m => m.name) : data;
        console.log(JSON.stringify(models, null, 2));
    } catch (e) {
        console.error(e);
    }
}
test();
