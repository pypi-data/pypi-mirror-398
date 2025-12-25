<script lang="ts">
  import { BlockTitle, Block } from "@gradio/atoms";
  import { onMount } from "svelte";
  import flatpickr from "flatpickr";
  import "flatpickr/dist/flatpickr.min.css";

  export let value: string | [string, string] | null = null;
  export let value_is_output = false;
  export let label: string;
  export let visible = true;
  export let elem_classes;
  export let elem_id;
  export let scale;
  export let info;
  export let min_width;
  export let show_label = true;
  export let container = true;
  export let interactive = true;
  export let gradio;
  export let mode: "single" | "range" = "single";
  export let date_format: string = "%Y-%m-%d";

  let el: HTMLInputElement;

  function handle_change(): void {
    gradio.dispatch("change");
    if (!value_is_output) {
      gradio.dispatch("input");
    }
  }

  function clear_value(): void {
    value = null;
    handle_change();
  }

  onMount(() => {
    const jsDateFormat = date_format
      .replace(/%Y/g, "Y")
      .replace(/%m/g, "m")
      .replace(/%d/g, "d");

    const options: flatpickr.Options.Options = {
      mode: mode === "range" ? "range" : "single",
      dateFormat: jsDateFormat,
      onChange: (_dates, dateStr: string) => {
        if (mode === "range") {
          value = dateStr.split(" to ");
        } else {
          value = dateStr;
        }
        handle_change();
      },
    };

    flatpickr(el, options);
  });

  $: value, handle_change();
</script>

<Block
  {visible}
  {elem_id}
  {elem_classes}
  {scale}
  {min_width}
  allow_overflow={false}
  padding={true}
>
  <label class:container>
    <BlockTitle {show_label} {info}>{label}</BlockTitle>
    <div class="input-with-clear">
      <input
        type="text"
        bind:this={el}
        bind:value={value}
        on:change={handle_change}
        disabled={!interactive}
      />
      {#if interactive && !value_is_output}
        <button class="clear-button" on:click={clear_value}>×</button>
      {/if}
    </div>
  </label>
</Block>

<style>
  label {
    display: block;
    width: 100%;
  }

  .input-with-clear {
    position: relative;
    display: flex;
    align-items: center;
    width: 100%;
  }

  input {
    display: block;
    position: relative;
    outline: none !important;
    box-shadow: var(--input-shadow);
    background: var(--input-background-fill);
    padding: var(--input-padding);
    width: 100%;
    color: var(--body-text-color);
    font-weight: var(--input-text-weight);
    font-size: var(--input-text-size);
    line-height: var(--line-sm);
    border: none;
    padding-right: 2.5rem; /* Make space for the clear button */
  }

  input:disabled {
    -webkit-text-fill-color: var(--body-text-color);
    -webkit-opacity: 1;
    opacity: 1;
  }

  .container > .input-with-clear > input {
    border: var(--input-border-width) solid var(--input-border-color);
    border-radius: var(--input-radius);
  }

  input:focus {
    box-shadow: var(--input-shadow-focus);
    border-color: var(--input-border-color-focus);
  }

  .clear-button {
    position: absolute;
    right: 0.5rem;
    top: 50%;
    transform: translateY(-50%);
    background: transparent;
    border: none;
    cursor: pointer;
    color: var(--body-text-color);
    font-size: 1.5rem;
    padding: 0;
    line-height: 1;
  }

  .clear-button:hover {
    color: var(--text-color-strong);
  }
</style>