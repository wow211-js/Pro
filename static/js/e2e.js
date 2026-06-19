// E2E Encryption using OpenPGP.js (ECC Curve25519)
const E2E = (() => {
    const getCsrf = () => document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
    let _keyCache = new Map();

    async function generateKeys(username, passphrase) {
        const { privateKey, publicKey } = await openpgp.generateKey({
            type: 'ecc', curve: 'curve25519',
            userIDs: [{ name: username }], passphrase,
        });
        return { privateKey, publicKey };
    }

    async function saveKeys(publicKey, privateKey) {
        const resp = await fetch('/api/keys/save/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
            body: JSON.stringify({ public_key: publicKey, encrypted_private_key: privateKey }),
        });
        return resp.json();
    }

    async function getPublicKey(username) {
        if (_keyCache.has(username)) return _keyCache.get(username);
        const resp = await fetch(`/api/keys/${username}/`);
        if (!resp.ok) return null;
        const data = await resp.json();
        _keyCache.set(username, data.public_key || null);
        return data.public_key || null;
    }

    async function getFingerprint(armoredPublicKey) {
        if (!armoredPublicKey) return null;
        try {
            const key = await openpgp.readKey({ armoredKey: armoredPublicKey });
            return key.getFingerprint().toUpperCase().match(/.{1,4}/g).join(' ');
        } catch { return null; }
    }

    async function encrypt(text, recipientPublicKeyArmored, senderPublicKeyArmored) {
        const keys = [await openpgp.readKey({ armoredKey: recipientPublicKeyArmored })];
        if (senderPublicKeyArmored && senderPublicKeyArmored !== recipientPublicKeyArmored) {
            keys.push(await openpgp.readKey({ armoredKey: senderPublicKeyArmored }));
        }
        return openpgp.encrypt({
            message: await openpgp.createMessage({ text }),
            encryptionKeys: keys,
        });
    }

    async function decrypt(ciphertext, privateKeyArmored, passphrase) {
        try {
            const privateKey = await openpgp.decryptKey({
                privateKey: await openpgp.readPrivateKey({ armoredKey: privateKeyArmored }),
                passphrase,
            });
            const { data } = await openpgp.decrypt({
                message: await openpgp.readMessage({ armoredMessage: ciphertext }),
                decryptionKeys: privateKey,
            });
            return data;
        } catch (e) {
            // Log specific error for debugging
            console.error('E2E decrypt failed:', e.message);
            return '[не удалось расшифровать: ' + e.message.slice(0, 60) + ']';
        }
    }

    async function verifyPassphrase(encryptedPrivateKey, passphrase) {
        try {
            await openpgp.decryptKey({
                privateKey: await openpgp.readPrivateKey({ armoredKey: encryptedPrivateKey }),
                passphrase,
            });
            return true;
        } catch { return false; }
    }

    function storeSession(encryptedPrivateKey, passphrase) {
        localStorage.setItem('e2e_passphrase', passphrase);
        localStorage.setItem('e2e_private_key', encryptedPrivateKey);
    }

    function getSession() {
        return {
            passphrase: localStorage.getItem('e2e_passphrase'),
            privateKey: localStorage.getItem('e2e_private_key'),
        };
    }

    return {
        generateKeys, saveKeys, getPublicKey, getFingerprint,
        encrypt, decrypt, verifyPassphrase, storeSession, getSession,
    };
})();
