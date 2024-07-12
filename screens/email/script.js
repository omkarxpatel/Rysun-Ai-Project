function App() {
            
    const [promptValue, setPromptValue] = React.useState('');
    const [noteValue, setNoteValue] = React.useState('');
    const [keywordValue, setKeywordValue] = React.useState('');
    const [selectedModel, setSelectedModel] = React.useState('');
    const [selectedTone, setSelectedTone] = React.useState('');
    const [selectedStyle, setSelectedStyle] = React.useState('');
    const [selectedLength, setSelectedLength] = React.useState('');
    const [selectedComplexity, setSelectedComplexity] = React.useState('');
    const [selectedOption, setSelectedOption] = React.useState('');
    const [selectedRole, setSelectedRole] = React.useState('');
    const [roleInfo, setRoleInfo] = React.useState('');

    const [aiResult, setAiResult] = React.useState('');
    const [gptSubject, setGptSubject] = React.useState('');
    const [gptResult, setGptResult] = React.useState('');
    const [metaResult, setMetaResult] = React.useState('')
    const [parameterizedPromptValue, setParameterizedPromptChange] = React.useState('');
    const [gptScore, setGptScore] = React.useState(2);
    const [metaScore, setMetaScore] = React.useState(2);
    const [bardScore, setBardScore] = React.useState(2);

    const [lastPrompt, setLastPrompt] = React.useState('');
    const [lastModel, setLastModel] = React.useState('');

    const [error, setError] = React.useState(null);
    const [loading, setLoading] = React.useState(false);
    const [serverStatus, setServerStatus] = React.useState(false);
    const [countdown, setCountdown] = React.useState(5);

    const[count, setCount] = React.useState(0);

    
    React.useEffect(() => {
        const checkServerStatus = () => {
        fetch('http://127.0.0.1:5000/api/status')
            .then(response => {
                if (response.ok) {
                    setServerStatus(true);

                    if (count == 0) {
                        setCount(1)
                        setError(null)
                    }
                    
                    setCountdown(5); // Reset the countdown when server is connected
                } else {
                    setCount(0)
                    setServerStatus(false);
                    setError('Server is not connected');
                }
            })
            .catch(error => {
                setServerStatus(false);
                setError('Server is not connected');
                console.error('Error checking server status:', error);
            });
    };
    
        const intervalId = setInterval(() => {
            setCountdown(prevCountdown => {
                console.log(gptResult)
                if (prevCountdown === 1) {
                    checkServerStatus();
                    return 5; // Reset countdown after checking server status
                }
                return prevCountdown - 1;
            });
        }, 1000);
    
        checkServerStatus(); // Initial check
    
        return () => clearInterval(intervalId);
    }, []);
    

    const handleModelChange = (e) => {
        const selectedValue = e.target.value;

        fetch('http://127.0.0.1:5000/api/model-dropdown-selected', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ selectedOption: selectedValue }),
        })
        .then(response => response.json())
        .then(data => {
            setAiResult('');
            setError(null);
            setSelectedModel(data.model);
            console.log('Dropdown selection response:', data);
        })
        .catch(error => console.error('Error calling dropdown selection API:', error));
    };

    const handleRoleChange = (e) => {
        const selectedValue = e.target.value;

        fetch('http://127.0.0.1:5000/api/role-dropdown-selected', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ selectedOption: selectedValue }),
        })
        .then(response => response.json())
        .then(data => {
            setSelectedRole(data.role);
            setRoleInfo(data.info)
            console.log('Dropdown selection response:', data);
        })
        .catch(error => console.error('Error calling dropdown selection API:', error));
    }

    const handleSelectionChange = (setter) => (e) => {
        const selectedValue = e.target.value;
        setter(selectedValue);
        setError(null)
        setLastPrompt("")


        fetch('http://127.0.0.1:5000/api/selection-choice', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ selectedOption: selectedValue }),
        })
        .then(response => response.json())
        .then(data => {
            console.log(data);
        })
        .catch(error => console.error('Error calling dropdown selection API:', error));
    };

    const handlePromptChange = (e) => {
        setPromptValue(e.target.value);

        if (error) {
            setError(null);
        }
    };

    const handleParameterizedPromptChange = (e) => {
        setParameterizedPromptChange(e.target.value);
    }

    const handleRoleInfoChange = (e) => {
        setRoleInfo(e.target.value)
    }

    const handleSliderChangeG = (event) => {
        setGptScore(event.target.value);
    };
    const handleSliderChangeM = (event) => {
        setMetaScore(event.target.value);
    };
    const handleSliderChangeB = (event) => {
        setBardScore(event.target.value);
    };

    const handleNoteChange = (e) => {
        setNoteValue(e.target.value);
        setError(null)
        setLastPrompt("")
    }

    const handleKeywordChange = (e) => {
        setKeywordValue(e.target.value);
        setError(null)
        setLastPrompt("")
    }

    const handlePromptSubmit = (e) => {
        e.preventDefault();
        console.log('Form submitted with user input:', promptValue);
    
        if (promptValue === '') setError("Please enter a prompt");
        else if (promptValue === lastPrompt && selectedModel === lastModel) setError("Please enter a new prompt or change models");
        else {
            console.log(promptValue);
            setLoading(true);
            setLastModel(selectedModel);
            setLastPrompt(promptValue);
            setError(null);
            setAiResult({ gptResponse: '', bardResponse: '', metaResponse: '' });
    
            fetch('http://127.0.0.1:5000/api/prompt-submission', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: promptValue, model: selectedModel, notes: noteValue, keywords: keywordValue , role: roleInfo}),
            })
            .then(() => {
                let eventSourceGpt = new EventSource('http://127.0.0.1:5000/api/stream-results/gpt');
                eventSourceGpt.onmessage = (e) => {
                    let temp = e.data;
                    const jsonData = JSON.parse(temp.replace('data: ', ''))

                    const title = jsonData["title"];
                    const content = jsonData["content"].replace(/`/g, "\n");
                    setAiResult(prevState => ({ ...prevState, gptTitle: title, gptResponse: content }));
                    eventSourceGpt.close();
                };
    
                let eventSourceBard = new EventSource('http://127.0.0.1:5000/api/stream-results/bard');
                eventSourceBard.onmessage = (e) => {
                    let temp = e.data;
                    const jsonData = JSON.parse(temp.replace('data: ', ''))

                    const title = jsonData["title"];
                    const content = jsonData["content"].replace(/`/g, "\n");
                    setAiResult(prevState => ({ ...prevState, bardTitle: title, bardResponse: content }));
                    eventSourceBard.close();
                };
    
                let eventSourceMeta = new EventSource('http://127.0.0.1:5000/api/stream-results/meta');
                eventSourceMeta.onmessage = (e) => {
                    let temp = e.data;
                    const jsonData = JSON.parse(temp.replace('data: ', ''))

                    const title = jsonData["title"];
                    const content = jsonData["content"].replace(/`/g, "\n\n");
                    setAiResult(prevState => ({ ...prevState, metaTitle: title, metaResponse: content }));
                    eventSourceMeta.close()
                    setLoading(false); // relies on the fact that meta is the slowest
                };
            })
            .catch(error => {
                console.error('Error calling prompt submission API:', error);
                setError(error.toString());
            })
        }
    };

    const handleGptRegenerate = (e) => {
        setLoading(true);
        setError(null);
    
        fetch('http://127.0.0.1:5000/api/gpt-regen', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(() => {
            let eventSourceGpt = new EventSource('http://127.0.0.1:5000/api/stream-results/gpt');
            eventSourceGpt.onmessage = (e) => {
                let temp = e.data;
                const jsonData = JSON.parse(temp.replace('data: ', ''))

                const title = jsonData["title"];
                const content = jsonData["content"].replace(/`/g, "\n");
                setAiResult(prevState => ({ ...prevState, gptTitle: title, gptResponse: content }));
                eventSourceGpt.close();
                setLoading(false);
            };
        })
        .catch(error => {
            console.error('Error calling GPT regeneration API:', error);
            setError(error.toString());
            setLoading(false);
        });
    }

    const handleGptRegenerateTitle = (e) => {
        setLoading(true);
        setError(null);

        fetch('http://127.0.0.1:5000/api/gpt-regen-title', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(aiResult)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === "Success") {
                setAiResult(prevState => ({ ...prevState, gptTitle: data.title }));
            } else {
                console.error('API returned error:', data.message);
                setError(data.message);
            }
            setLoading(false);
        })
        .catch(error => {
            console.error('Error calling GPT title regeneration API:', error);
            setError(error.toString());
            setLoading(false);
        });
    };
    
    const handleBardRegenerateTitle = (e) => {
        setLoading(true);
        setError(null);
        
        fetch('http://127.0.0.1:5000/api/bard-regen-title', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(aiResult)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === "Success") {
                setAiResult(prevState => ({ ...prevState, bardTitle: data.title }));
            } else {
                console.error('API returned error:', data.message);
                setError(data.message);
            }
            setLoading(false);
        })
        .catch(error => {
            console.error('Error calling Bard title regeneration API:', error);
            setError(error.toString());
            setLoading(false);
        });
    };

    const handleMetaRegenerateTitle = (e) => {
        setLoading(true);
        setError(null);
        
        fetch('http://127.0.0.1:5000/api/meta-regen-title', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(aiResult)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === "Success") {
                setAiResult(prevState => ({ ...prevState, metaTitle: data.title }));
            } else {
                console.error('API returned error:', data.message);
                setError(data.message);
            }
            setLoading(false);
        })
        .catch(error => {
            console.error('Error calling Meta title regeneration API:', error);
            setError(error.toString());
            setLoading(false);
        });
    };

    const handleBardRegenerate = (e) => {
        setLoading(true);
        setError(null);
    
        fetch('http://127.0.0.1:5000/api/bard-regen', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(() => {
            let eventSourceBard = new EventSource('http://127.0.0.1:5000/api/stream-results/bard');
            eventSourceBard.onmessage = (e) => {
                let temp = e.data;
                const jsonData = JSON.parse(temp.replace('data: ', ''))

                const title = jsonData["title"];
                const content = jsonData["content"].replace(/`/g, "\n");
                setAiResult(prevState => ({ ...prevState, bardTitle: title, bardResponse: content }));
                eventSourceBard.close();
                setLoading(false);
            };
        })
        .catch(error => {
            console.error('Error calling Bard regeneration API:', error);
            setError(error.toString());
            setLoading(false);
        });
    }

    const handleMetaRegenerate = (e) => {
        setLoading(true);
        setError(null);
    
        fetch('http://127.0.0.1:5000/api/meta-regen', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(() => {
            let eventSourceMeta = new EventSource('http://127.0.0.1:5000/api/stream-results/meta');
            eventSourceMeta.onmessage = (e) => {
                let temp = e.data;
                const jsonData = JSON.parse(temp.replace('data: ', ''))

                const title = jsonData["title"];
                const content = jsonData["content"].replace(/`/g, "\n");
                setAiResult(prevState => ({ ...prevState, metaTitle: title, metaResponse: content }));
                eventSourceMeta.close();
                setLoading(false);
            };
        })
        .catch(error => {
            console.error('Error calling Meta regeneration API:', error);
            setError(error.toString());
            setLoading(false);
        });
    }    
    
    
    const handleRegenerate = (type) => {
        setLoading(true);
        setError(null);
    
        const promptType = type === "title" ? "Regenerate Title of this email but keep the text the exact same"+aiResult : "Regenerate Text of this email but keep the title the exact same"+aiResult;
        const prompt = `${promptValue} -- ${promptType}`;
    
        fetch('http://127.0.0.1:5000/api/prompt-submission', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ prompt, model: selectedModel , notes: noteValue, keywords: keywordValue }),
        })
        .then(response => response.json())
        .then(responseData => {
            if (responseData.response === 'Please select a model') setError("Please select a model");
            else if (responseData.response.substring(0, 6) === "Error:") setError(responseData.response);
            else setAiResult(responseData);
            console.log('API response:', responseData);
        })
        .catch(error => {
            console.error('Error calling prompt submission API:', error);
            setError(error.toString());
        })
        .finally(() => {
            setLoading(false);
        });
    };
    
    const handleOptionChange = (e) => {
        setSelectedOption(e.target.value);
        setError(null);
        setLastPrompt("");
    
        fetch('http://127.0.0.1:5000/api/selection-choice', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ selectedOption: e.target.value }),
        })
        .then(response => response.json())
        .then(data => {
            console.log(data);
        })
        .catch(error => console.error('Error calling selection choice API:', error));
    };
}