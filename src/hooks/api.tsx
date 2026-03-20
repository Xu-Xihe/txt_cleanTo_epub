import ky from "ky"


export const api = ky.create({
    timeout: 5000,
    retry: 0,
    headers: {
        "Content-Type": "application/json"
    },
});