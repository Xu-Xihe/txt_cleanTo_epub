import { Box, Skeleton } from "@mui/material";
import "./loading.css";




export function LoadingEditor({ text }: { text: string }) {
    return (
        <Box sx={{
            position: "absolute",
            top: 0,
            left: 188,
            right: 0,
            bottom: 0,
            display: "flex",
            flexDirection: "row",
            justifyContent: "center",
            alignItems: "center",
            zIndex: 8888,
            p: 3,
            gap: 1,
            bgcolor: (theme) => theme.vars?.palette.background.default,
        }}>
            {text === ""
                ? (<>
                    <Skeleton variant="rounded" width="50%" height="100%" />
                    <Skeleton variant="rounded" width="50%" height="100%" />
                </>)
                : text
            }
        </Box>
    );
}

export function LoadingFullScreen() {
    return (
        <Box sx={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            zIndex: 8888,
            p: 3,
            bgcolor: (theme) => theme.vars?.palette.background.default,
        }}>
            <Skeleton variant="rounded" height="100%" sx={{ width: 188, mr: 3 }} />
            <Skeleton variant="rounded" height="100%" sx={{ width: "100%" }} />
        </Box>
    );
}