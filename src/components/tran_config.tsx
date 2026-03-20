import {
    Box,
    Button,
    Divider,
    FormGroup,
    Paper,
    FormControlLabel,
    Switch,
    Typography,
} from "@mui/material";
import DoneAllRoundedIcon from '@mui/icons-material/DoneAllRounded';

import { useState } from "react";

import { api } from "../hooks/api";
import { useErrorMsg } from "../components/error_popout";

import useLocalStorage from "../hooks/storage";
import AppleSuccess from "./Success";


interface TranConfig {
    save_txt: boolean;
    del_origin: boolean;
}


export default function TranConfig() {
    const { pushMsg } = useErrorMsg();
    const [tranConfig, setTranConfig] = useLocalStorage<TranConfig>("tranconfig", { save_txt: false, del_origin: false }, "local")
    const [isLoading, setIsLoading] = useState<boolean>(false)
    const [isSuccess, setIsSuccess] = useState<boolean>(false)

    const executeTran = () => {
        setIsLoading(true)
        api.post("/api/tran/execute", { json: { tranConfig } }).json<string[]>()
            .then((data) => {
                setIsLoading(false)
                if (data.length > 0) {
                    for (var i = 0; i < data.length; i += 1) {
                        pushMsg("File: " + data[i])
                    }
                }
                else { setIsSuccess(true) }
            })
            .catch((error) => {
                pushMsg("Failed to execute tran: " + error);
                setIsLoading(false)
            })
    }

    return (
        <>
            {isSuccess && <AppleSuccess />}
            <Paper elevation={13} sx={{
                width: "80%",
                height: "80%",
                p: 0,
                m: 0,
            }}>
                <Box sx={{
                    display: "flex",
                    flexDirection: "column",
                    height: "100%",
                    width: "100%",
                    justifyContent: "space-evenly",
                    px: 8
                }}>
                    <Typography variant="h4">
                        转换配置
                    </Typography>
                    <Divider flexItem />
                    <FormGroup>
                        <FormControlLabel control={
                            <Switch
                                checked={tranConfig.save_txt}
                                onChange={(e) => setTranConfig({
                                    save_txt: e.target.checked,
                                    del_origin: tranConfig.del_origin,
                                })}
                            />
                        } label="保存txt文件" />
                        <FormControlLabel control={
                            <Switch
                                checked={tranConfig.del_origin}
                                onChange={(e) => setTranConfig({
                                    save_txt: tranConfig.save_txt,
                                    del_origin: e.target.checked,
                                })}
                            />
                        } label="删除源文件" />
                    </FormGroup>
                    <Divider flexItem />
                    <Box sx={{ display: 'flex', width: '100%', justifyContent: "flex-end" }}>
                        <Button
                            variant="contained"
                            sx={{ gap: 1 }}
                            startIcon={<DoneAllRoundedIcon />}
                            loadingPosition="end"
                            loading={isLoading}
                            onClick={() => executeTran()}
                        >
                            确定
                        </Button>
                    </Box>
                </Box>
            </Paper>
        </>
    )
}