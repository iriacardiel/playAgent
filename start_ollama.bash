#!/bin/bash

export OLLAMA_MODELS=/opt/.ollama-dori/models
export OLLAMA_KEEP_ALIVE=24h
echo "OLLAMA_MODELS:" $OLLAMA_MODELS
echo "OLLAMA_KEEP_ALIVE:" $OLLAMA_KEEP_ALIVE
ollama serve

