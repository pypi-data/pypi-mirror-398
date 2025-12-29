"""Example script demonstrating debug streaming gateway usage.

This script shows how to test the streaming pipeline locally without
requiring Kafka, Redis, or API connectivity.
"""

import logging
import time
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from matrice_streaming.streaming_gateway.debug import DebugStreamingGateway, DebugStreamingAction


def example_basic_streaming():
    """Basic example: Stream a single video file."""
    print("\n" + "="*80)
    print("Example 1: Basic Streaming")
    print("="*80 + "\n")
    
    # Specify your video file path
    video_path = "path/to/your/video.mp4"
    
    if not Path(video_path).exists():
        print(f"⚠️  Video file not found: {video_path}")
        print("Please update the video_path variable with a valid video file path.")
        return
    
    # Create debug gateway
    gateway = DebugStreamingGateway(
        video_paths=[video_path],
        fps=10,
        video_codec="h265-frame",
        loop_videos=True,
        log_messages=True,
        save_to_files=False
    )
    
    print(f"✓ Gateway created: {gateway}")
    
    # Start streaming
    print("\nStarting streaming...")
    gateway.start_streaming()
    
    # Let it run for 10 seconds
    print("Streaming for 10 seconds...")
    time.sleep(10)
    
    # Check statistics
    stats = gateway.get_statistics()
    print("\n📊 Statistics:")
    print(f"  Frames sent: {stats['transmission_stats']['frames_sent_full']}")
    print(f"  Messages sent: {stats['backend_stats']['total_messages']}")
    print(f"  Runtime: {stats['runtime_seconds']:.1f}s")
    
    # Stop streaming
    print("\nStopping streaming...")
    gateway.stop_streaming()
    print("✓ Streaming stopped")


def example_multiple_videos():
    """Example with multiple video files."""
    print("\n" + "="*80)
    print("Example 2: Multiple Video Streams")
    print("="*80 + "\n")
    
    video_paths = [
        "path/to/video1.mp4",
        "path/to/video2.mp4",
        "path/to/video3.mp4"
    ]
    
    # Check if files exist
    existing_videos = [v for v in video_paths if Path(v).exists()]
    if not existing_videos:
        print("⚠️  No video files found. Please update video_paths with valid files.")
        return
    
    print(f"Found {len(existing_videos)} video files")
    
    # Create gateway with multiple streams
    gateway = DebugStreamingGateway(
        video_paths=existing_videos,
        fps=10,
        video_codec="h265-frame",
        loop_videos=True,
        log_messages=True
    )
    
    # Start streaming
    gateway.start_streaming()
    
    # Monitor for 20 seconds
    for i in range(4):
        time.sleep(5)
        stats = gateway.get_statistics()
        print(f"\n📊 Stats at {(i+1)*5}s:")
        print(f"  Total frames sent: {stats['transmission_stats']['frames_sent_full']}")
        print(f"  Active streams: {stats['transmission_stats']['active_streams']}")
    
    gateway.stop_streaming()
    print("\n✓ All streams stopped")


def example_save_to_files():
    """Example: Save streamed messages to files."""
    print("\n" + "="*80)
    print("Example 3: Save Messages to Files")
    print("="*80 + "\n")
    
    video_path = "path/to/your/video.mp4"
    
    if not Path(video_path).exists():
        print(f"⚠️  Video file not found: {video_path}")
        return
    
    # Create gateway that saves messages to files
    gateway = DebugStreamingGateway(
        video_paths=[video_path],
        fps=5,  # Lower FPS for fewer files
        video_codec="h265-frame",
        loop_videos=False,  # Don't loop
        save_to_files=True,
        output_dir="./debug_stream_output",
        log_messages=True,
        save_frame_data=False  # Don't save large frame data
    )
    
    print("✓ Gateway created with file saving enabled")
    print("   Output directory: ./debug_stream_output")
    
    # Start streaming
    gateway.start_streaming()
    
    # Stream for 15 seconds
    print("\nStreaming for 15 seconds...")
    time.sleep(15)
    
    # Stop and show results
    gateway.stop_streaming()
    
    stats = gateway.get_statistics()
    print("\n📊 Final Statistics:")
    print(f"  Total messages: {stats['backend_stats']['total_messages']}")
    print(f"  Output directory: ./debug_stream_output")
    print(f"  Check ./debug_stream_output/messages/ for saved message files")
    print(f"  Check ./debug_stream_output/summary.json for summary")


def example_with_streaming_action():
    """Example: Using DebugStreamingAction."""
    print("\n" + "="*80)
    print("Example 4: Using DebugStreamingAction")
    print("="*80 + "\n")
    
    video_path = "path/to/your/video.mp4"
    
    if not Path(video_path).exists():
        print(f"⚠️  Video file not found: {video_path}")
        return
    
    # Use context manager for automatic cleanup
    with DebugStreamingAction(
        video_paths=[video_path],
        fps=10,
        video_codec="h265-frame",
        save_to_files=True,
        output_dir="./debug_action_output"
    ) as action:
        print("✓ Debug action created")
        
        # Start
        action.start()
        print("✓ Streaming started")
        
        # Monitor
        for i in range(3):
            time.sleep(5)
            status = action.get_status()
            print(f"\n📊 Status at {(i+1)*5}s: {status['transmission_stats']['frames_sent_full']} frames")
        
        # Stop (automatic on context exit)
        print("\nStopping (automatic cleanup)...")
    
    print("✓ Action stopped and cleaned up")


def example_custom_resolution():
    """Example: Custom resolution and codec settings."""
    print("\n" + "="*80)
    print("Example 5: Custom Resolution and Codec")
    print("="*80 + "\n")
    
    video_path = "path/to/your/video.mp4"
    
    if not Path(video_path).exists():
        print(f"⚠️  Video file not found: {video_path}")
        return
    
    # Test different codecs
    codecs = ["h265-frame", "h265-chunk", "h264"]
    
    for codec in codecs:
        print(f"\nTesting codec: {codec}")
        
        gateway = DebugStreamingGateway(
            video_paths=[video_path],
            fps=10,
            video_codec=codec,
            width=320,  # Downscale to 320x240
            height=240,
            h265_quality=28,  # Higher quality value = lower quality
            loop_videos=False,
            log_messages=False,  # Less verbose
            save_to_files=False
        )
        
        gateway.start_streaming()
        time.sleep(5)
        
        stats = gateway.get_statistics()
        print(f"  Frames sent: {stats['transmission_stats']['frames_sent_full']}")
        print(f"  Codec: {stats['transmission_stats']['video_codec']}")
        
        gateway.stop_streaming()


def main():
    """Run all examples (or selected ones)."""
    print("="*80)
    print("Debug Streaming Gateway Examples")
    print("="*80)
    print("\n⚠️  IMPORTANT: Update video file paths before running!")
    print("\nAvailable examples:")
    print("  1. Basic streaming")
    print("  2. Multiple video streams")
    print("  3. Save messages to files")
    print("  4. Using DebugStreamingAction")
    print("  5. Custom resolution and codecs")
    print("\n")
    
    # Run examples (comment out the ones you don't want to run)
    try:
        example_basic_streaming()
        # example_multiple_videos()
        # example_save_to_files()
        # example_with_streaming_action()
        # example_custom_resolution()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("Examples completed!")
    print("="*80)


if __name__ == "__main__":
    main()

