"""Example usage of GluRPC client."""
from glucosedao_client import GluRPCClient, GluRPCConfig
import plotly.graph_objects as go


def main():
    """Example of using the GluRPC client programmatically."""
    
    # Configure client
    config = GluRPCConfig(
        base_url="http://localhost:8000",
        api_key=None  # Set if your server requires it
    )
    
    # Create client
    client = GluRPCClient(config)
    
    try:
        # 1. Check server health
        print("🔍 Checking server health...")
        health = client.health()
        print(f"   Status: {health.status}")
        print(f"   Load status: {health.load_status}")
        print(f"   Models initialized: {health.models_initialized}")
        print(f"   Device: {health.device}")
        print(f"   Cache size: {health.cache_size}")
        print(f"   Total HTTP requests: {health.total_http_requests}")
        print(f"   Total HTTP errors: {health.total_http_errors}")
        print()
        
        # 2. Convert a raw CGM file to unified format
        print("📁 Converting file to unified format...")
        raw_file_path = "path/to/your/dexcom_export.csv"
        
        convert_response = client.convert_to_unified(raw_file_path)
        
        if convert_response.error:
            print(f"   ❌ Conversion failed: {convert_response.error}")
            return
        
        print(f"   ✅ Converted successfully")
        print()
        
        # 3. Process the unified CSV
        print("⚙️  Processing unified data...")
        process_response = client.process_unified(
            convert_response.csv_content,
            force_calculate=False  # Use cache if available
        )
        
        if process_response.error:
            print(f"   ❌ Processing failed: {process_response.error}")
            return
        
        print(f"   ✅ Processed successfully")
        print(f"   Handle: {process_response.handle}")
        print(f"   Total samples: {process_response.total_samples}")
        
        if process_response.warnings and process_response.warnings.get('has_warnings'):
            print(f"   ⚠️  Warnings detected:")
            for msg in process_response.warnings.get('messages', []):
                print(f"      - {msg}")
        print()
        
        # 4. Generate plots for different samples
        print("📊 Generating prediction plots...")
        
        # The server uses negative indexing where 0 = most recent sample
        # We need to convert from positive (0-based) to negative indexing
        total_samples = process_response.total_samples
        
        # Plot the most recent sample (server index 0)
        plot_data = client.draw_plot(
            handle=process_response.handle,
            index=0,  # Most recent sample
            force_calculate=False
        )
        
        # Convert to Plotly figure and save as HTML
        fig = go.Figure(plot_data)
        output_file = "prediction_most_recent.html"
        fig.write_html(output_file)
        
        print(f"   ✅ Saved plot to {output_file}")
        
        # Plot a few more samples using negative indexing
        # -1 = second-to-last, -5 = 5 samples back from end
        for server_index in [-5, -10]:
            plot_data = client.draw_plot(
                handle=process_response.handle,
                index=server_index,
                force_calculate=False
            )
            
            fig = go.Figure(plot_data)
            output_file = f"prediction_sample_{server_index}.html"
            fig.write_html(output_file)
            
            print(f"   ✅ Saved plot to {output_file}")
        
        print()
        
        # 5. Check cache info
        print("💾 Cache management...")
        cache_info = client.cache_management("info")
        print(f"   Cache size: {cache_info.get('cache_size', 0)}")
        print(f"   Persisted count: {cache_info.get('persisted_count', 0)}")
        print()
        
        # 6. Alternative: Use quick_plot for one-off analysis
        print("⚡ Testing quick_plot (process + plot in one call)...")
        quick_response = client.quick_plot(
            convert_response.csv_content,
            force_calculate=False
        )
        
        if quick_response.error:
            print(f"   ❌ Quick plot failed: {quick_response.error}")
        else:
            fig = go.Figure(quick_response.plot_data)
            fig.write_html("quick_plot_result.html")
            print(f"   ✅ Quick plot saved to quick_plot_result.html")
        print()
        
        print("✅ All done!")
        
    finally:
        # Always close the client
        client.close()


if __name__ == "__main__":
    main()

