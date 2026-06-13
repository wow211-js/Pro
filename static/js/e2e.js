// E2E Encryption using OpenPGP.js
// Keys are generated in browser, private key encrypted with user password

const E2E = {
    async generateKeys(username, passphrase) {
        const { privateKey, publicKey } = await openpgp.generateKey({
            type: 'rsa',
            rsaBits: 2048,
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
                'X-CSRFToken': document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '',
            },
            body: JSON.stringify({
                public_key: publicKey,
                encrypted_private_key: privateKey,
            }),
        });
        return resp.json();
    },

    async getPublicKey(username) {
        const resp = await fetch(`/api/keys/${username}/`);
        if (!resp.ok) return null;
        const data = await resp.json();
        return data.public_key;
    },

    async encrypt(text, recipientPublicKeyArmored, senderPublicKeyArmored) {
        const recipientKey = await openpgp.readKey({ armoredKey: recipientPublicKeyArmored });
        const senderKey = await openpgp.readKey({ armoredKey: senderPublicKeyArmored });
        const encrypted = await openpgp.encrypt({
            message: await openpgp.createMessage({ text }),
            encryptionKeys: [recipientKey, senderKey], // encrypt for both so sender can read too
        });
        return encrypted;
    },

    async decrypt(ciphertext, privateKeyArmored, passphrase) {
        try {
            const privateKey = await openpgp.decryptKey({
                privateKey: await openpgp.readPrivateKey({ armoredKey: privateKeyArmored }),
                passphrase,
            });
            const message = await openpgp.readMessage({ armoredMessage: ciphertext });
            const { data } = await openpgp.decrypt({
                message,
                decryptionKeys: privateKey,
            });
            return data;
        } catch (e) {
            return '[не удалось расшифровать]';
        }
    },

    storeSession(encryptedPrivateKey, passphrase) {
        // Store passphrase only in sessionStorage (cleared when tab closes)
        sessionStorage.setItem('e2e_passphrase', passphrase);
        sessionStorage.setItem('e2e_private_key', encryptedPrivateKey);
    },

    getSession() {
        return {
            passphrase: sessionStorage.getItem('e2e_passphrase'),
            privateKey: sessionStorage.getItem('e2e_private_key'),
        };
    },

    clearSession() {
        sessionStorage.removeItem('e2e_passphrase');
        sessionStorage.removeItem('e2e_private_key');
    },
};
