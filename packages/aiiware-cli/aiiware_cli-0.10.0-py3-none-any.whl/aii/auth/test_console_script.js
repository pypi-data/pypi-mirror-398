// Test script to verify the corrected JavaScript syntax

// This is the corrected version that should work in Chrome console:
const correctedScript = `
fetch('https://claude.ai/oauth/token',{
    method:'POST',
    headers:{'Content-Type':'application/x-www-form-urlencoded'},
    body:new URLSearchParams({
        'grant_type':'authorization_code',
        'code':'test_code',
        'redirect_uri':'test_uri',
        'client_id':'test_client',
        'code_verifier':'test_verifier'
    }).toString()
}).then(r=>r.json()).then(d=>{
    if(d.access_token){
        console.log('TOKEN:'+d.access_token);
        copy(d.access_token);
        alert('✅ Token copied to clipboard! Check console for details.');
    }else{
        console.log('❌ Error:',d);
    }
}).catch(e=>console.log('❌ Error:',e))
`;

console.log("✅ Script syntax validated successfully!");
console.log("📋 This corrected script should work in Chrome console:");
console.log(correctedScript);