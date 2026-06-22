// E2E Encryption using OpenPGP.js (ECC Curve25519)

const E2E = {
    async generateKeys(username, passphrase) {
        const { privateKey, publicKey } = await openpgp.generateKey({
            type: 'ecc',
            curve: 'curve25519',
            userIDs: [{ name: username }],
            passphrase: passphrase,
        });
        return { privateKey, publicKey };
    },

    async saveKeys(publicKey, privateKey) {
        const resp = await fetch('/api/keys/save/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': (document.cookie.match(/csrftoken=([^;]+)/) || [])[1] || '',
            },
            body: JSON.stringify({ public_key: publicKey, encrypted_private_key: privateKey }),
        });
        return resp.json();
    },

    async getPublicKey(username) {
        const resp = await fetch(`/api/keys/${username}/`);
        if (!resp.ok) return null;
        const data = await resp.json();
        return data.public_key || null;
    },

    async getFingerprint(armoredPublicKey) {
        try {
            const key = await openpgp.readKey({ armoredKey: armoredPublicKey });
            const fp = key.getFingerprint().toUpperCase();
            return fp.match(/.{1,4}/g).join(' ');
        } catch(e) { return null; }
    },

    async encrypt(text, recipientPublicKeyArmored, senderPublicKeyArmored) {
        const keys = [await openpgp.readKey({ armoredKey: recipientPublicKeyArmored })];
        if (senderPublicKeyArmored && senderPublicKeyArmored !== recipientPublicKeyArmored)
            keys.push(await openpgp.readKey({ armoredKey: senderPublicKeyArmored }));
        return await openpgp.encrypt({
            message: await openpgp.createMessage({ text }),
            encryptionKeys: keys,
        });
    },

    async decrypt(ciphertext, privateKeyArmored, passphrase) {
        try {
            const privateKey = await openpgp.decryptKey({
                privateKey: await openpgp.readPrivateKey({ armoredKey: privateKeyArmored }),
                passphrase,
            });
            const message = await openpgp.readMessage({ armoredMessage: ciphertext });
            const { data } = await openpgp.decrypt({ message, decryptionKeys: privateKey });
            return data;
        } catch(e) { return '[не удалось расшифровать]'; }
    },

    storeSession(encryptedPrivateKey, passphrase) {
        localStorage.setItem('e2e_passphrase', passphrase);
        localStorage.setItem('e2e_private_key', encryptedPrivateKey);
    },

    getSession() {
        return {
            passphrase: localStorage.getItem('e2e_passphrase'),
            privateKey: localStorage.getItem('e2e_private_key'),
        };
    },
};
