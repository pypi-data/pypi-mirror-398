#!/bin/bash
rm -r dist
uv build
uv publish
