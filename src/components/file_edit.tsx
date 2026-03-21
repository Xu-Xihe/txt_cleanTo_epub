import {
    Box,
    Dialog,
    DialogContent,
    DialogTitle,
    DialogActions,
    Divider,
    TextField,
    List,
    ListItemButton,
    ListItemText,
    Button,
    useMediaQuery,
} from "@mui/material";
import { useColorScheme } from '@mui/material/styles';
import SyncRoundedIcon from '@mui/icons-material/SyncRounded';
import DoneAllRoundedIcon from '@mui/icons-material/DoneAllRounded';
import EditRoundedIcon from '@mui/icons-material/EditRounded';

import { useEffect, useState, useRef } from "react";

import Editor from '@monaco-editor/react';
import * as monaco from "monaco-editor";

import { api } from "../hooks/api";
import { useErrorMsg } from "../components/error_popout";
import { LoadingEditor, LoadingCard } from "./loading";


interface FileName {
    name: string;
    title: string;
    creator: string;
    desc?: string;
    source?: string;
}
const BUFFER = 200;


export default function FileList({ setStep }: { setStep: (step: number) => void }) {
    // Define Value
    const { pushMsg } = useErrorMsg();
    const [lsFile, setLsFile] = useState<FileName[]>([]);
    const [fileSelect, setFileSelect] = useState<FileName>({ name: "", title: "", creator: "" });
    const [executing, setExecuting] = useState<boolean>(false);
    const [fileSelected, setFileSelected] = useState<number>(0);
    const [openMdaEditor, setOpenMdaEditor] = useState<boolean>(false);
    const { mode } = useColorScheme();
    const isDark = useMediaQuery("(prefers-color-scheme: dark)");

    const maxLine = useRef<number>(null);
    const controller = useRef<AbortController | null>(null);
    const srollTimeoutRef = useRef<NodeJS.Timeout>(null);
    const orgEditor = useRef<monaco.editor.IStandaloneCodeEditor>(null);
    const mdfEditor = useRef<monaco.editor.IStandaloneCodeEditor>(null);
    const editorAPI = useRef<typeof monaco.editor>(null);
    const [refreshEditor, setRefreshEditor] = useState<number>(0);


    // Function Part
    const file_read = async (filename: string) => {
        try {
            const data = await api.get("/api/file/read", { searchParams: { filename } }).json<number>();
            maxLine.current = data;
        } catch (error) {
            pushMsg("Failed to read file: " + error);
        }
    }

    const update_mda = (data: FileName) => {
        api.post("/api/file/update", { json: data }).json()
            .catch((error) => { pushMsg("Failed to update metadata: " + error); })
    }


    const handleScroll = (init: boolean) => {
        if (!maxLine.current) {
            return;
        }
        const visibleRange = (orgEditor.current?.getVisibleRanges()[0] as monaco.Range);

        const start_line = init
            ? 1
            : visibleRange.startLineNumber;

        const end_line = init
            ? Math.min(maxLine.current, BUFFER)
            : Math.min(maxLine.current, visibleRange.endLineNumber + BUFFER);

        const total_line = orgEditor.current?.getModel()?.getLineCount() ?? 0;

        if (controller.current) {
            controller.current.abort();
        }
        controller.current = new AbortController();

        api.get("/api/file/get", {
            searchParams: { start_line, end_line },
            signal: controller.current.signal
        }).json<Record<string, string[]>>()
            .then((data) => {
                if (init) {
                    orgEditor.current?.getModel()?.setValue(data["origin"].join("\n"));
                }
                else {
                    if (end_line <= total_line) {
                        orgEditor.current?.getModel()?.applyEdits([{
                            range: {
                                startLineNumber: start_line,
                                startColumn: 1,
                                endLineNumber: end_line,
                                endColumn: init ? 1 : orgEditor.current.getModel()?.getLineMaxColumn(end_line) ?? 1
                            },
                            text: data["origin"].join("\n"),
                        }]);
                    }
                    else {
                        orgEditor.current?.getModel()?.applyEdits([{
                            range: {
                                startLineNumber: start_line,
                                startColumn: 1,
                                endLineNumber: total_line,
                                endColumn: init ? 1 : orgEditor.current.getModel()?.getLineMaxColumn(total_line) ?? 1
                            },
                            text: data["origin"].slice(0, total_line - start_line + 1).join("\n") + "\n",
                        }]);
                        orgEditor.current?.getModel()?.applyEdits([{
                            range: {
                                startLineNumber: total_line + 1,
                                startColumn: 1,
                                endLineNumber: total_line + 1,
                                endColumn: 1
                            },
                            text: data["origin"].slice(total_line - start_line + 1).join("\n"),
                        }]);
                    }
                }
                mdfEditor.current?.getModel()?.setValue(data["format"].join("\n"));
            })
            .catch((error) => {
                if ((error as Error).name !== "AbortError") {
                    pushMsg("Failed to fetch file content: " + error);
                }
            })
        mdfEditor.current?.setScrollTop(0);
    }




    // Fetch file list eachtime path changes.
    useEffect(() => {
        api.get("/api/file/ls").json<FileName[]>()
            .then((data) => { setLsFile(data); })
            .catch((error) => { pushMsg("获取文件列表失败: " + (error as Error).message); })
    }, []);

    useEffect(() => {
        if (!editorAPI.current) return;
        if (mode === "system") {
            editorAPI.current?.setTheme(isDark ? "myvs-dark" : "myvs");
        }
        else if (mode === "dark") {
            editorAPI.current?.setTheme("myvs-dark");
        }
        else {
            editorAPI.current?.setTheme("myvs");
        }
    }, [mode, fileSelected]);


    return (
        <>
            {executing && <LoadingCard list={lsFile.map((f) => f.name)} path="/api/file/execute" next={() => setStep(2)} cancel={() => setExecuting(false)} />}
            <Dialog open={openMdaEditor} onClose={() => { setOpenMdaEditor(false); }} maxWidth={false}>
                <DialogTitle>编辑作品元数据: {fileSelect.name}</DialogTitle>
                <DialogContent>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
                        {[["title", "标题"], ["creator", "作者"], ["desc", "描述"], ["source", "来源"]].map(([key, label]) => (
                            <TextField
                                key={key}
                                label={label}
                                value={fileSelect[key as keyof FileName]}
                                required={key === "title"}
                                onChange={(e) => {
                                    setFileSelect({ ...fileSelect, [key]: e.target.value });
                                }}
                                multiline={key === "desc"}
                                sx={{ width: '60vw' }}
                            />
                        ))}
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => {
                        setOpenMdaEditor(false);
                        setFileSelect(lsFile.find((item) => item.name === fileSelect.name) ?? { name: "", title: "", creator: "" });
                    }} variant="outlined">取消</Button>
                    <Button onClick={() => {
                        setOpenMdaEditor(false);
                        update_mda(fileSelect);
                        setLsFile((prev) => prev.map((item) => item.name === fileSelect.name ? fileSelect : item));
                    }} variant="contained">确定</Button>
                </DialogActions>
            </Dialog>
            <List sx={{ minWidth: 188, maxWidth: 188, overflow: "auto", height: '100%' }}>
                {lsFile.map((item) => (
                    <>
                        <ListItemButton
                            key={item.name}
                            onClick={() => {
                                setFileSelected(1);
                                file_read(item.name)
                                    .then(() => {
                                        setFileSelected(2);
                                        setFileSelect(item);
                                        setRefreshEditor(Date.now());
                                    })
                            }}
                        >
                            <ListItemText primary={item.name} secondary={
                                <>
                                    标题: {item.title}
                                    <br />
                                    作者: {item.creator}
                                </>
                            } />
                        </ListItemButton>
                        <Divider variant="middle" />
                    </>
                ))}
            </List>
            <Divider orientation="vertical" flexItem />
            <Box sx={{
                width: 'calc(100% - 188px)', height: '100%',
                display: 'flex', justifyContent: 'center', alignItems: 'center', flexDirection: 'column',
            }}>
                {fileSelected < 2 && <LoadingEditor text={fileSelected === 0 ? "请选择一个文件进行编辑" : ""} />}
                <>
                    <Box sx={{ display: 'flex', gap: 3, width: '100%', justifyContent: 'space-between', alignItems: 'center', px: 3, my: 1 }}>
                        <Box sx={{ display: 'flex', gap: 3 }}>
                            <TextField
                                size="small"
                                label={"name"}
                                variant="outlined"
                                value={fileSelect.name}
                                disabled
                            />
                            {[["标题", "title"], ["作者", "creator"]].map(([label, key]) => (
                                <TextField
                                    key={key}
                                    size="small"
                                    label={label}
                                    variant="outlined"
                                    value={fileSelect[key as keyof FileName]}
                                    required={key === "title"}
                                    onChange={(e) => {
                                        setFileSelect({ ...fileSelect, [key]: e.target.value });
                                        if (e.target.value) {
                                            update_mda({ ...fileSelect, [key]: e.target.value });
                                            setLsFile((prev) => prev.map((item) => item.name === fileSelect.name ? { ...item, [key]: e.target.value } : item));
                                        }
                                    }}
                                />
                            ))}
                        </Box>
                        <Divider orientation="vertical" flexItem />
                        <Box sx={{ display: 'flex', gap: 8 }}>
                            <Button
                                variant="outlined"
                                startIcon={<SyncRoundedIcon />}
                                sx={{ gap: 1 }}
                                onClick={() => setRefreshEditor(Date.now())}
                            >
                                刷新
                            </Button>
                            <Button
                                variant="outlined"
                                startIcon={<EditRoundedIcon />}
                                sx={{ gap: 1 }}
                                onClick={() => setOpenMdaEditor(true)}
                            >
                                编辑元数据
                            </Button>
                        </Box>
                        <Divider orientation="vertical" flexItem />
                        <Button
                            variant="contained"
                            startIcon={<DoneAllRoundedIcon />}
                            sx={{ gap: 1 }}
                            onClick={() => setExecuting(true)}
                        >
                            开始格式化
                        </Button>
                    </Box>
                    <Box key={fileSelect.name + refreshEditor} sx={{
                        width: "100%",
                        height: "100%",
                        flexDirection: 'row',
                        display: 'flex',
                    }}>
                        <Editor
                            height="100%"
                            width="50%"
                            language="text"
                            theme="myvs"
                            options={{
                                readOnly: true,
                                wordWrap: "on",
                                lineNumbers: "on",
                                smoothScrolling: true,
                                scrollBeyondLastLine: false,
                                minimap: { enabled: false },
                                renderLineHighlight: "none",
                                renderWhitespace: "none",
                                lineNumbersMinChars: 3,
                                mouseWheelZoom: false,
                                unicodeHighlight: {
                                    nonBasicASCII: false,
                                    ambiguousCharacters: false,
                                    invisibleCharacters: false,
                                },
                                automaticLayout: true,
                            }}
                            onMount={(editor, api) => {
                                orgEditor.current = editor;

                                api.languages.register({ id: 'clearDiff' });
                                api.languages.setMonarchTokensProvider('clearDiff', {
                                    defaultToken: 'text',
                                    tokenizer: {
                                        root: [
                                            // # 开头的行
                                            [/^#.*$/, 'hashLine'],
                                            // <div 开头的行
                                            [/^<div.*$/, 'divLine'],
                                            // 其他默认
                                            [/.+/, 'text'],
                                        ],
                                    },
                                });
                                api.editor.defineTheme('myvs', {
                                    base: 'vs',
                                    inherit: true,
                                    rules: [
                                        { token: 'hashLine', foreground: '81D8D0', fontStyle: 'bold' },
                                        { token: 'divLine', foreground: '33FFD6', fontStyle: 'bold italic' },
                                    ],
                                    colors: {},
                                });
                                api.editor.defineTheme('myvs-dark', {
                                    base: 'vs-dark',
                                    inherit: true,
                                    rules: [
                                        { token: 'hashLine', foreground: 'F8CDCD', fontStyle: 'bold' },
                                        { token: 'divLine', foreground: '33FFD6', fontStyle: 'bold italic' },
                                    ],
                                    colors: {},
                                });


                                editor.setModel(api.editor.createModel("", "text/plain"));

                                editor.onDidScrollChange(() => {
                                    if (srollTimeoutRef.current) {
                                        clearTimeout(srollTimeoutRef.current);
                                    }
                                    srollTimeoutRef.current = setTimeout(handleScroll, 300, false);
                                });
                            }}
                        />
                        <Editor
                            height="100%"
                            width="50%"
                            language="clearDiff"
                            theme="myvs"
                            options={{
                                readOnly: true,
                                wordWrap: "on",
                                lineNumbers: "off",
                                smoothScrolling: true,
                                scrollBeyondLastLine: false,
                                minimap: { enabled: false },
                                unicodeHighlight: {
                                    nonBasicASCII: false,
                                    ambiguousCharacters: false,
                                    invisibleCharacters: false,
                                },
                                mouseWheelZoom: false,
                                automaticLayout: true,
                            }}
                            onMount={(editor, api) => {
                                mdfEditor.current = editor;
                                editorAPI.current = api.editor;
                                editor.setModel(api.editor.createModel("", "clearDiff"));
                                setTimeout(handleScroll, 0, true);
                            }}
                        />
                    </Box>
                </>
            </Box>
        </>
    );
};