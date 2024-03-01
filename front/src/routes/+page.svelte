<script lang="ts">
    import { io } from "socket.io-client";
    import { onMount, type ComponentType } from "svelte";

    // Type Gymnastics
    interface Track {
        status: "playing" | "ended" | "looping" | "paused";
        audio: string;
    }
    const SERVER_ADDRESS = `http://${import.meta.env.IPADDR}:6942`;
    let AUDIO_LIST: string[] | null = null;
    let PLAYING: Track[] | null = null;
    let CONNECTED = true;
    let DARK_MODE = true;
    let container: HTMLDivElement | null = null;
    let volumeSlider: HTMLInputElement | null = null;
    onMount(() =>
        setInterval(async () => {
            fetch(SERVER_ADDRESS + "/update", {
                method: "GET",
                mode: "cors"
            })
                .then((response) => {
                    response.json().then((a) => {
                        AUDIO_LIST = a.available;
                        PLAYING = a.playing;
                        CONNECTED = true;
                    });
                })
                .catch((_) => {
                    CONNECTED = false;
                });
        }, 200)
    );
    const socket = io(SERVER_ADDRESS, {
        transports: ["websocket"]
    });
    const requestAudioFunction = (audioName: string) => () => {
        socket.emit("play_audio", audioName);
        PLAYING?.push({
            status: "playing",
            audio: audioName
        });
    };

    const audioOperation = (opName: string, trackIndex: number) => () => {
        socket.emit("audio_operation", {
            operation: opName,
            value: trackIndex
        });
    };
    const toggleMode = () => {
        DARK_MODE = !DARK_MODE;
    };

    const volumeChange = () => {
        let sliderValue = volumeSlider?.value;
        if (sliderValue) {
            socket.emit("audio_operation", {
                operation: "volume",
                value: Number.parseFloat(sliderValue)
            });
        }
    };

    $: {
        if (container) {
            if (DARK_MODE) {
                container.classList.add("dark-mode");
            } else {
                container.classList.remove("dark-mode");
            }
        }
    }
</script>

<div id="container" class="dark-mode" bind:this={container}>
    <div class="topbar">
        <p>Soundboard</p>
        <button class="ldbutton" on:click={toggleMode}>{DARK_MODE ? "Light" : "Dark"}</button>
    </div>
    <div class="lower">
        <div class="pad">
            {#if AUDIO_LIST === null || !CONNECTED}
                <p class="noresponse">Đang kết nối...</p>
            {:else if AUDIO_LIST.length > 0}
                {#each AUDIO_LIST as audioName}
                    <button on:click={requestAudioFunction(audioName)}
                        >{audioName.substring(0, audioName.length - 4)}</button
                    >
                {/each}
            {:else}
                <p class="noresponse">Không có tệp âm thanh nào.</p>
            {/if}
        </div>
        <div class="playing">
            <p class="label">CURRENTLY PLAYING</p>
            <p class="sublabel">Click on entries to fade.</p>
            {#if !CONNECTED}
                <p class="noresponse">Đang kết nối...</p>
            {:else if PLAYING === null}
                <p class="noresponse">Hiện không phát âm thanh nào</p>
            {:else if PLAYING.length > 0}
                {#each PLAYING.entries() as [i, track]}
                    <button class="playing-entry" on:click={audioOperation("fade", i)}>
                        <p>{track.audio.substring(0, track.audio.length - 4)}</p>
                        <div>
                            <button class="smallbtn" on:click={audioOperation("pause", i)}>
                                {#if track.status == "paused"}
                                    Resume
                                {:else}
                                    Pause
                                {/if}
                            </button>
                            <!-- <button class="smallbtn" on:click={audioOperation("fade", i)}
                                >Fade</button
                            > -->
                            <button class="smallbtn" on:click={audioOperation("stop", i)}
                                >Stop</button
                            >
                            <!-- <button class="smallbtn" on:click={audioOperation("togloop", i)}
                                >{#if track.status == "looping"}
                                    Unloop
                                {:else}
                                    Loop
                                {/if}</button
                            > -->
                        </div>
                    </button>
                {/each}
            {:else}
                <p class="noresponse">Không có tệp âm thanh nào đang phát.</p>
            {/if}
        </div>
    </div>
    <div class="slidecon">
        <input
            type="range"
            min="0"
            max="1"
            value="1"
            step="0.001"
            class="slider"
            id="volume"
            on:input={volumeChange}
            bind:this={volumeSlider}
        />
    </div>
</div>

<style>
    :root {
        --font: "Plus Jakarta Sans", "SF Pro Text", "SF Pro Display", system-ui, -apple-system,
            BlinkMacSystemFont, "Helvetica Neue", "Segoe UI Variable Display", "Segoe UI", Tahoma,
            Geneva, Roboto, Verdana, sans-serif;
        --accent: #d833af;
        --text-color: #000000;
        --text-color-2: #ffffff;
        --text-color-3: #2e3440;
        --fade-color: #2e3440;
        --accent-text: #ffffff;
        --background-color: #ffffff;
    }

    .dark-mode {
        --background-color: #1c1f26;
        --accent: #ad288c;
        --text-color: #ffffff;
        --text-color-2: #ffffff;
        --text-color-3: #b48ead;
        --fade-color: #2e3440;
        --accent-text: #ffffff;
    }

    #container {
        font-family: var(--font);
        color: var(--text-color);
        background-color: var(--background-color);
        margin-top: 0;
        height: 100vh;
        width: 100%;
    }
    .topbar {
        border-bottom: solid 2px var(--fade-color);
        background-color: var(--accent);
        color: #ffffff;
        font-weight: bold;
        text-align: center;
        display: flex;
        justify-content: space-between;
        padding: 1em 2em 1em 2em;
        margin-bottom: 1em;
        align-items: center;
    }

    .topbar p {
        font-size: 1.5em;
    }

    .lower {
        display: flex;
        flex-direction: row;
    }
    .pad {
        width: 70%;
        height: calc(100vh - 9em);
        overflow-y: scroll;
        overflow-wrap: normal;
        display: flex;
        flex-direction: row;
        flex-wrap: wrap;
        margin: 1em 1em 0 1em;
        border-right: dashed 1px var(--fade-color);
    }
    .noresponse {
        text-align: center;
        margin: auto;
        margin-top: 30vh;
        color: var(--text-color-3);
    }
    .pad button {
        font-family: var(--font);
        font-weight: bold;
        border: solid 2px var(--fade-color);
        background-color: var(--fade-color);
        color: var(--text-color-2);
        border-radius: 9px;
        padding: 3em;
        width: max-content;
        margin-right: 0.5em;
        margin-bottom: 0.5em;
        cursor: pointer;
    }

    .label {
        color: var(--text-color-3);
        font-weight: bold;
        text-align: center;
        margin-bottom: 2em;
    }

    .playing {
        width: 30%;
        margin-right: 2em;
        height: 80vh;
        overflow: scroll;
    }

    .playing-entry {
        display: flex;
        flex-direction: row;
        border: none;
        background: none;
        width: 100%;
        border-bottom: dashed 1px var(--fade-color);
        padding: 1em;
        align-items: center;
        justify-content: space-between;
        font-family: var(--font);
        font-size: 1em;
        color: var(--text-color);
        cursor: pointer;
    }

    .smallbtn {
        border: none;
        padding: 10px;
        background: var(--accent);
        margin-left: 0.5em;
        border-radius: 6px;
        font-family: var(--font);
        font-weight: bold;
        transition: ease-in-out 200ms;
        color: var(--accent-text);
    }

    .smallbtn:hover {
        backdrop-filter: brightness(80%);
    }

    .ldbutton {
        font-family: var(--font);
        font-weight: bold;
        border: solid 2px var(--fade-color);
        background-color: var(--fade-color);
        color: var(--text-color-1);
        border-radius: 9px;
        padding: 0.5em;
        width: max-content;
        cursor: pointer;
    }

    .slidecon {
        width: 100%;
        height: 7vh;
        margin: auto;
        display: flex;
        align-items: center;
        justify-content: center;
        justify-items: center;
        margin-top: -0.5em;
    }

    .slider {
        width: 95%;
        height: 2em;
        -webkit-appearance: none;
        appearance: none;
        outline: none;
        opacity: 0.7; /* Set transparency (for mouse-over effects on hover) */
        background: var(--fade-color);
        -webkit-transition: 0.2s; /* 0.2 seconds transition on hover */
        transition: ease-in 0.2s;
        border-radius: 13px;
    }

    .slider::-webkit-slider-thumb {
        -webkit-appearance: none; /* Override default look */
        appearance: none;
        width: 30px; /* Set a specific slider handle width */
        height: 30px; /* Slider handle height */
        background: var(--accent); /* Green background */
        cursor: pointer; /* Cursor on hover */
        border-radius: 30px;
    }

    .slider::-moz-range-thumb {
        width: 30px; /* Set a specific slider handle width */
        height: 30px; /* Slider handle height */
        background: var(--accent); /* Green background */
        cursor: pointer; /* Cursor on hover */
        border-radius: 30px;
    }
    .sublabel {
        text-align: center;
        width: 100%;
        font-style: italic;
        margin-top: -1.5em;
        color: var(--text-color-3);
    }
</style>
