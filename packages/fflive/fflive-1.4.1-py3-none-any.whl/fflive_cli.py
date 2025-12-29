#!/usr/bin/python2.7
# coding=utf-8
"""
FFLive - Command Line Interface
This allows using fflive like: fflive [options] [input] [output]
"""

import sys
import os
import subprocess
import argparse
from fflive import stream

def main():
    parser = argparse.ArgumentParser(description='FFLive - Stream processing with authentication')
    parser.add_argument('-i', '--input', help='Input file or URL', required=True)
    parser.add_argument('-c:v', '--video-codec', dest='vcodec', help='Video codec')
    parser.add_argument('-c:a', '--audio-codec', dest='acodec', help='Audio codec')
    parser.add_argument('-preset', '--preset', help='Encoding preset')
    parser.add_argument('-b:v', '--video-bitrate', dest='vbitrate', help='Video bitrate')
    parser.add_argument('-b:a', '--audio-bitrate', dest='abitrate', help='Audio bitrate')
    parser.add_argument('-f', '--format', help='Output format')
    parser.add_argument('-filter_complex', '--filter-complex', help='Filter complex string')
    parser.add_argument('-user_agent', '--user-agent', help='User agent string')
    parser.add_argument('-referer', '--referer', help='Referer header')
    parser.add_argument('-headers', '--headers', help='Additional headers in format "Header1:Value1,Header2:Value2"')
    parser.add_argument('-key', '--key', help='Stream key or authentication key')
    parser.add_argument('output', help='Output URL or file')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Create stream instance
    st = stream.Stream()
    
    # Set input
    st.input(args.input)
    
    # Set video codec if provided
    if args.vcodec:
        st.vcode(args.vcodec)
    
    # Set RTMP output with key if provided
    if args.key:
        st.rtmp_output(args.output, key=args.key)
    else:
        st.rtmp_output(args.output)
    
    # Set additional parameters
    if args.preset:
        st.set_video_preset(args.preset)
    if args.vbitrate:
        st.set_video_bitrate(args.vbitrate)
    if args.acodec:
        # We need to handle this differently since acodec is passed as a full parameter
        # For now, we'll store it as a custom parameter
        st.acode_type = f"-c:a {args.acodec}"
    if args.abitrate:
        st.set_audio_bitrate(args.abitrate)
    if args.format:
        st.set_format(args.format)
    
    # Set authentication headers
    if args.user_agent:
        st.set_user_agent(args.user_agent)
    if args.referer:
        st.set_referer(args.referer)
    if args.headers:
        # Parse headers in format "Header1:Value1,Header2:Value2"
        header_pairs = args.headers.split(',')
        for pair in header_pairs:
            if ':' in pair:
                name, value = pair.split(':', 1)
                st.set_header(name.strip(), value.strip())
    
    # For filter_complex, we need to parse it and apply the appropriate effects
    # This is a simplified version - in a real implementation you'd want to parse the filter complex
    if args.filter_complex:
        print(f"Note: Filter complex '{args.filter_complex}' would be processed here")
        # In a full implementation, you'd parse the filter_complex string and apply effects
    
    print(f"Starting stream from {args.input} to {args.output}")
    print("Stream configuration:")
    print(f"  Input: {args.input}")
    print(f"  Output: {args.output}")
    if args.vcodec: print(f"  Video codec: {args.vcodec}")
    if args.acodec: print(f"  Audio codec: {args.acodec}")
    if args.preset: print(f"  Preset: {args.preset}")
    if args.vbitrate: print(f"  Video bitrate: {args.vbitrate}")
    if args.abitrate: print(f"  Audio bitrate: {args.abitrate}")
    if args.format: print(f"  Format: {args.format}")
    if args.user_agent: print(f"  User agent: {args.user_agent}")
    if args.referer: print(f"  Referer: {args.referer}")
    if args.key: print(f"  Key: {args.key[:20]}...")
    
    # Run the stream
    try:
        st.run()
        print("Stream completed successfully!")
    except Exception as e:
        print(f"Error running stream: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()