import os
import json
import time
from typing import Optional, Dict, Any, List
from mcp_use.agents.mcpagent import MCPAgent
from langfuse.langchain import CallbackHandler
from langfuse import get_client,observe
from langchain_core.callbacks import BaseCallbackHandler


def init_env():

    TRINITY_PUBLIC_KEY=os.getenv("TRINITY_PUBLIC_KEY")
    TRINITY_SECRET_KEY=os.getenv("TRINITY_SECRET_KEY")
    TRINITY_HOST=os.getenv("TRINITY_HOST")

    os.environ["LANGFUSE_PUBLIC_KEY"] = TRINITY_PUBLIC_KEY
    os.environ["LANGFUSE_SECRET_KEY"] = TRINITY_SECRET_KEY
    os.environ["LANGFUSE_HOST"] = TRINITY_HOST






@observe
def upload_trace_with_span(trace_data, langfuse_trace_id=None):
    

    try:
        print(f"Uploading formatted trace data as span")
        print(f"Trace ID: {langfuse_trace_id}")
        return {
            "status": "completed",
            "trace_id": langfuse_trace_id,
            "formatted_trace_data": trace_data,
            "upload_timestamp": time.time()
        }
    except Exception as e:
        print(f"Error in upload_trace_with_span: {e}")
        return {"status": "error", "error": str(e), "trace_id": langfuse_trace_id}

# Initialize Langfuse client
langfuse_client = get_client()

class ToolCaptureCallback(BaseCallbackHandler):    
    def __init__(self):
        self.tool_executions = []
        self.current_tools = {}  
        
    def on_tool_start(self, serialized, input_str, **kwargs):
        tool_name = serialized.get("name", "unknown_tool")
        tool_id = kwargs.get("run_id", f"{tool_name}_{len(self.tool_executions)}")
        
        self.current_tools[tool_id] = {
            "name": tool_name,
            "input": input_str,
            "output": None,
            "start_time": time.time(),
            "error": None,
            "tool_id": tool_id
        }
        print(f"Tool started: {tool_name} (ID: {tool_id})")
        
    def on_tool_end(self, output, **kwargs):
        """Called when a tool finishes executing"""
        tool_id = kwargs.get("run_id")
        if tool_id and tool_id in self.current_tools:
            tool_exec = self.current_tools[tool_id]
            tool_exec["output"] = output
            tool_exec["end_time"] = time.time()
            tool_exec["duration"] = tool_exec["end_time"] - tool_exec["start_time"]
            self.tool_executions.append(tool_exec)
            print(f"Tool completed: {tool_exec['name']} (ID: {tool_id}) - Output length: {len(str(output))}")
            del self.current_tools[tool_id]
        else:
            # Fallback: if no tool_id, use the last tool
            if self.current_tools:
                tool_id = list(self.current_tools.keys())[-1]
                tool_exec = self.current_tools[tool_id]
                tool_exec["output"] = output
                tool_exec["end_time"] = time.time()
                tool_exec["duration"] = tool_exec["end_time"] - tool_exec["start_time"]
                self.tool_executions.append(tool_exec)
                print(f"Tool completed (fallback): {tool_exec['name']} - Output length: {len(str(output))}")
                del self.current_tools[tool_id]
            
    def on_tool_error(self, error, **kwargs):
        """Called when a tool execution fails"""
        tool_id = kwargs.get("run_id")
        if tool_id and tool_id in self.current_tools:
            tool_exec = self.current_tools[tool_id]
            tool_exec["error"] = str(error)
            tool_exec["end_time"] = time.time()
            tool_exec["duration"] = tool_exec["end_time"] - tool_exec["start_time"]
            self.tool_executions.append(tool_exec)
            print(f"Tool error: {tool_exec['name']} (ID: {tool_id}) - {error}")
            del self.current_tools[tool_id]
        else:
            # Fallback: if no tool_id, use the last tool
            if self.current_tools:
                tool_id = list(self.current_tools.keys())[-1]
                tool_exec = self.current_tools[tool_id]
                tool_exec["error"] = str(error)
                tool_exec["end_time"] = time.time()
                tool_exec["duration"] = tool_exec["end_time"] - tool_exec["start_time"]
                self.tool_executions.append(tool_exec)
                print(f"Tool error (fallback): {tool_exec['name']} - {error}")
                del self.current_tools[tool_id]
            
    def get_tool_executions(self):
        """Get all captured tool executions"""
        return self.tool_executions.copy()
class MonitoringWrapper:
    def __init__(self, agent: MCPAgent, project_name: str = "MCP-Agent-Monitor"):
        init_env()
        self.agent = agent
        self.project_name = project_name
        self.langfuse_client = langfuse_client
        self.langfuse_handler = CallbackHandler()
        self.tool_callback = ToolCaptureCallback()  
        self.trace_data = []
        self.last_trace_id = None
        self.last_span_id = None  
        self.last_execution_time = None
        self.last_duration = None
    
    def _capture_tools_info(self) -> List[Dict[str, Any]]:
        """Capture information about available tools"""
        tools_info = []
        
        try:
            if hasattr(self.agent, '_tools') and self.agent._tools:
                for tool in self.agent._tools:
                    tool_info = {
                        "name": getattr(tool, 'name', 'Unknown'),
                        "description": getattr(tool, 'description', 'No description available'),
                        "type": getattr(tool, '__class__.__name__', 'Unknown'),
                        "args_schema": str(getattr(tool, 'args_schema', 'No schema available'))
                    }
                    tools_info.append(tool_info)
        except Exception as e:
            print(f"⚠️  Could not capture tools info: {e}")
            
        return tools_info
    @observe
    async def run(self, query: str) -> str:

        print(f"Processing query: {query}")
        
        # Start timing for trace
        start_time = time.time()
        
        try:
            # Initialize the agent first
            await self.agent.initialize()
            inputs = {
                "input": query,
                "chat_history": [],  
                "agent_scratchpad": []  
            }
            
            # Clear previous tool executions
            self.tool_callback.tool_executions = []
            
            # Run the agent with both Langfuse and custom tool callbacks
            if self.agent._agent_executor:
                result = await self.agent._agent_executor.ainvoke(
                    inputs, 
                    return_only_outputs=True,
                    config={"callbacks": [self.langfuse_handler, self.tool_callback]}
                )
                # Extract the result from the agent executor response
                if isinstance(result, dict) and "output" in result:
                    print(f"Agent executor returned result: {result}")
                    result = result["output"]
            else:
                # Fallback to regular run method if executor is not available
                print("No executor available, using fallback method")
                result = await self.agent.run(query)
            
            # Calculate execution time
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000  
            duration = end_time - start_time
            
            # Store timing information
            self.last_execution_time = execution_time
            self.last_duration = duration
            
            print(f"Result: {result}")
            
            # Get trace information
            trace_id = self.langfuse_handler.last_trace_id
            if trace_id:
                self.last_trace_id = trace_id
                print(f"Trace captured successfully!")
                print(f"Trace ID: {trace_id}")
                print(f"Execution time: {execution_time:.2f}ms")
                print(f"Tools available: {len(self.agent._tools) if hasattr(self.agent, '_tools') else 'Unknown'}")
                
                # Flush events to ensure they're sent to Langfuse
                self.langfuse_client.flush()
                print(f"Trace data flushed to Langfuse")
                
                # Wait a bit for trace to be processed
                print("Waiting for trace processing...")
                time.sleep(3)
                
                # Use the custom tool callback data instead of trying to extract from trace
                try:
                    trace_result = self._create_trace_data_with_captured_tools(
                        trace_id=trace_id,
                        query=query,
                        result=result,
                        start_time=start_time,
                        end_time=end_time,
                        execution_time=execution_time,
                        duration=duration
                    )
                    
                    if trace_result["success"]:
                        print("Trace data processing completed successfully")
                    else:
                        print("Trace data processing completed with warnings")
                        
                except Exception as e:
                    print(f"Could not process trace data: {e}")
                    # Save error information in the same formatted file
                    error_trace_data = [
                        {
                            "run_data": {
                                "run_id": trace_id,
                                "name": "MCP Agent Run",
                                "status": "error",
                                "inputs": {
                                    "input": query
                                },
                                "outputs": {
                                    "result": result
                                },
                                "error": str(e),
                                "start_time": start_time,
                                "end_time": end_time,
                                "latency": execution_time,
                                "duration": duration,
                                "tools_info": self._capture_tools_info()
                            },
                            "Tool_runs": [],
                            "Chain_runs": [],
                            "detailed_trace": {
                                "trace_id": trace_id,
                                "name": "MCP Agent Run",
                                "execution_time_ms": execution_time,
                                "error": str(e),
                                "note": "Error occurred during trace processing"
                            }
                        }
                    ]
                    with open("formatted_trace_data.json", "w", encoding="utf-8") as f:
                        json.dump(error_trace_data, f, indent=2, default=str)
                    print(f"Error trace data saved to formatted_trace_data.json")
                
            else:
                print("No trace data captured")
            
            return {"result":result,"traceId":trace_id}
            
        except Exception as e:
            print(f"Error in run function: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            # Ensure all events are flushed before exiting
            try:
                self.langfuse_client.flush()
                print("Final flush completed")
            except:
                pass
    
    def _create_trace_data_with_captured_tools(self, trace_id, query, result, start_time, end_time, execution_time, duration):
        """Create trace data using captured tool executions from custom callback"""
        print(f"Creating trace data with captured tool executions for ID: {trace_id}")
        
        # Get captured tool executions from our custom callback
        captured_tools = self.tool_callback.get_tool_executions()
        print(f"Found {len(captured_tools)} captured tool executions")
        
        # Debug: Print details of each captured tool
        for i, tool_exec in enumerate(captured_tools):
            print(f"Tool {i+1}: {tool_exec['name']}")
            print(f"   Input: {tool_exec['input']}")
            print(f"   Output length: {len(str(tool_exec['output']))}")
            print(f"   Duration: {tool_exec.get('duration', 0):.2f}s")
            print(f"   Error: {tool_exec.get('error', 'None')}")
        
        # Create tools_info array
        tools_info = self._capture_tools_info()
        
        # Convert captured tool executions to the expected format
        tool_runs = []
        for tool_exec in captured_tools:
            tool_run = {
                "name": tool_exec["name"],
                "tool_input": tool_exec["input"],
                "tool_output": tool_exec["output"],
                "duration": tool_exec.get("duration", 0),
                "error": tool_exec.get("error", None)
            }
            tool_runs.append(tool_run)
            print(f"Added tool run: {tool_exec['name']} - Output length: {len(str(tool_exec['output']))}")
        
        # Fallback: If we didn't capture all tools via callback, try to get them from agent
        if len(tool_runs) < 2 and hasattr(self.agent, '_agent_executor') and self.agent._agent_executor:
            print(f"Only captured {len(tool_runs)} tools via callback, checking agent intermediate steps...")
            try:
                # Try to get intermediate steps from the agent executor
                if hasattr(self.agent._agent_executor, 'intermediate_steps'):
                    intermediate_steps = self.agent._agent_executor.intermediate_steps
                    print(f"Found {len(intermediate_steps)} intermediate steps in agent")
                    
                    for step in intermediate_steps:
                        if isinstance(step, list) and len(step) >= 2:
                            action, observation = step[0], step[1]
                            if hasattr(action, 'tool'):
                                # Check if this tool is already captured
                                tool_name = action.tool
                                already_captured = any(tool_run["name"] == tool_name for tool_run in tool_runs)
                                
                                if not already_captured:
                                    tool_run = {
                                        "name": tool_name,
                                        "tool_input": action.tool_input,
                                        "tool_output": str(observation),
                                        "duration": 0,  # We don't have timing for this
                                        "error": None
                                    }
                                    tool_runs.append(tool_run)
                                    print(f"Added tool run from intermediate steps: {tool_name}")
            except Exception as e:
                print(f"Could not get intermediate steps: {e}")
        
        # Try to get cost and token information from Langfuse trace
        cost_info = {
            "total_cost": 0.0,
            "total_tokens": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_breakdown": [],
            "token_breakdown": [],
            "note": "Cost information not available from custom callback capture"
        }
        
        # Try to get the actual trace from Langfuse to extract cost info
        try:
            full_trace = self.langfuse_client.api.trace.get(trace_id)
            # Use the trace object directly instead of calling get_observations
            cost_info = {
                "total_cost": 0.0,
                "total_tokens": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost_breakdown": [],
                "token_breakdown": [],
                "note": "Cost extraction simplified - using trace object directly"
            }
        except Exception as e:
            print(f"Could not get trace for cost extraction: {e}")
        
        # Create comprehensive trace data
        trace_data = {
            "trace_id": trace_id,
            "name": "MCP Agent Run",
            "user_id": None,
            "session_id": None,
            "tags": [],
            "input": {"input": query},
            "output": {"result": result},
            "timestamp": time.time(),
            "execution_time_ms": execution_time,
            "tools_used": len(captured_tools),
            "intermediate_steps": [],
            "note": "Tool outputs captured via custom callback",
            "cost_info": cost_info  # Add cost and token information
        }
        
        # Create formatted trace data with all information consolidated
        formatted_trace_data = [
            {
                "run_data": {
                    "run_id": trace_id,
                    "name": "MCP Agent Run",
                    "status": "success",
                    "inputs": {
                        "input": query
                    },
                    "outputs": {
                        "result": result
                    },
                    "error": None,
                    "start_time": start_time,
                    "end_time": end_time,
                    "latency": execution_time,
                    "duration": duration,
                    "tools_info": tools_info,
                    "cost_info": cost_info  # Add cost and token information to run_data
                },
                "Tool_runs": tool_runs,
                "Chain_runs": [],
                "detailed_trace": trace_data
            }
        ]
        

        try:
            formatted_trace_data=formatted_trace_data[0]
            upload_result = upload_trace_with_span(formatted_trace_data, langfuse_trace_id=trace_id)
            if upload_result and "trace_id" in upload_result:
                print(f"Formatted trace uploaded as span successfully!")

 
                self.last_span_id = upload_result.get("trace_id")
            else:
                print("Failed to upload formatted trace as span")
            langfuse_client.flush()
        except Exception as e:
            print(f"Could not upload span: {e}")
        
        print(f"Comprehensive trace data saved to formatted_trace_data.json")
        print(f"Trace ID: {trace_id}")
        print(f"Tool runs captured: {len(tool_runs)}")
        
        return {
            "success": True,
            "tool_runs": tool_runs,
            "tools_info": tools_info,
            "formatted_data": formatted_trace_data,
            "trace_data": trace_data
        }
    


def monitoring_wrapper(agent: MCPAgent, project_name: str = "MCP-Agent-Monitor") -> MonitoringWrapper:
    """
    Simple function to wrap an MCP agent with monitoring
    """
    
    return MonitoringWrapper(agent, project_name) 