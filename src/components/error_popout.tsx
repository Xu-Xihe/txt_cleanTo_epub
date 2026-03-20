import { Alert, IconButton, Snackbar, Box } from "@mui/material";
import CloseRoundedIcon from '@mui/icons-material/CloseRounded';
import { create } from "zustand";

interface ErrorMsgState {
    msg: string[];
    pushMsg: (text: string) => void;
    delMsg: (text: string) => void;
}

export const useErrorMsg = create<ErrorMsgState>((set) => ({
    msg: [],

    pushMsg: (text) => {

        set((state) => {
            const list = [...state.msg, text];

            return {
                msg: list.slice(-8)
            };
        });

        setTimeout(() => {
            set((state) => ({
                msg: state.msg.filter((m) => m !== text)
            }));
        }, 8000);

    },

    delMsg: (text) => {
        set((state) => ({
            msg: state.msg.filter((m) => m !== text)
        }));
    },

}));

export default function ErrorPopout() {
    const { msg, delMsg } = useErrorMsg();

    return (
        <>
            {msg.map((m, i) => (
                <Snackbar
                    key={i + m}
                    open
                >
                    <Alert
                        variant="filled"
                        severity="error"
                        sx={{ alignItems: "center" }}
                    >
                        <Box sx={{
                            width: 288,
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "space-between",
                            flexDirection: "row",
                            fontSize: 16,
                        }}>
                            <Box sx={{ display: "flex" }}>
                                {m}
                            </Box>
                            <IconButton
                                size="small"
                                onClick={() => delMsg(m)}
                            >
                                <CloseRoundedIcon fontSize="small" />
                            </IconButton>
                        </Box>
                    </Alert>
                </Snackbar>
            ))}
        </>
    );
}