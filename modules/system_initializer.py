"""
System Initializer - Graceful Degradation and Fallback Management

This module handles system initialization with comprehensive fallback detection
and user-friendly messages when components are unavailable.

Requirements: 8.7, 11.9, 17.16
Task: 17.3 - Implement graceful degradation and fallback mechanisms

Fallback behaviors:
1. If Porcupine unavailable → Fallback to keyword-based wake word detection
2. If Ollama unavailable → Fallback to Gemini
3. If VB-Cable not installed → Switch to BASIC_MODE automatically  
4. If CareCam SDK unavailable → Use UI automation (CareCam_Controller)
5. Display informative messages when fallbacks are activated
"""

import logging
import sys
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

# Setup logging
logger = logging.getLogger(__name__)


class ComponentStatus(Enum):
    """Status of system components"""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    FALLBACK_ACTIVE = "fallback_active"
    NOT_CHECKED = "not_checked"


@dataclass
class ComponentInfo:
    """Information about a system component"""
    name: str
    status: ComponentStatus
    fallback_name: Optional[str] = None
    message: str = ""
    is_critical: bool = False


@dataclass
class SystemStatus:
    """Overall system initialization status"""
    initialized: bool
    components: Dict[str, ComponentInfo]
    warnings: List[str]
    errors: List[str]
    fallbacks_activated: List[str]


class SystemInitializer:
    """
    System Initializer with graceful degradation support.
    
    Responsibilities:
    - Check availability of optional components
    - Activate fallback mechanisms when needed
    - Display informative messages about system configuration
    - Configure operation mode based on available resources
    """
    
    def __init__(self):
        """Initialize the system initializer"""
        self.components: Dict[str, ComponentInfo] = {}
        self.warnings: List[str] = []
        self.errors: List[str] = []
        self.fallbacks_activated: List[str] = []
        
        logger.info("SystemInitializer created")
    
    def initialize_system(self, config) -> SystemStatus:
        """
        Initialize all system components with fallback detection.
        
        Args:
            config: System configuration object
            
        Returns:
            SystemStatus with initialization results
        """
        print("\n" + "=" * 70)
        print("🚀 Initializing Tỷ Tỷ Chatbot System with Fallback Detection")
        print("=" * 70 + "\n")
        
        # Check all components
        self._check_wake_word_engine(config)
        self._check_ai_service(config)
        self._check_vb_cable(config)
        self._check_carecam_sdk(config)
        
        # Display summary
        self._display_initialization_summary()
        
        # Determine if system can start
        initialized = self._can_start_system()
        
        return SystemStatus(
            initialized=initialized,
            components=self.components.copy(),
            warnings=self.warnings.copy(),
            errors=self.errors.copy(),
            fallbacks_activated=self.fallbacks_activated.copy()
        )
    
    def _check_wake_word_engine(self, config) -> None:
        """
        Check Porcupine availability, fallback to keyword matching if unavailable.
        
        Requirement: 11.9 - If Porcupine not available, fallback to keyword matching
        """
        print("🔊 [1/4] Checking Wake Word Engine...")
        
        try:
            # Try to import Porcupine
            import pvporcupine
            porcupine_available = True
        except ImportError:
            porcupine_available = False
        
        if porcupine_available and config.WAKE_WORD_ENGINE_ENABLED:
            # Porcupine is available
            self.components["wake_word_engine"] = ComponentInfo(
                name="Wake Word Engine",
                status=ComponentStatus.AVAILABLE,
                message="Porcupine acoustic model"
            )
            print("   ✅ Porcupine acoustic model available")
            print(f"   📍 Sensitivity: {config.WAKE_WORD_SENSITIVITY}")
            print(f"   📂 Model path: {config.WAKE_WORD_MODEL_PATH}")
        else:
            # Fallback to keyword matching
            self.components["wake_word_engine"] = ComponentInfo(
                name="Wake Word Engine",
                status=ComponentStatus.FALLBACK_ACTIVE,
                fallback_name="Keyword Matching",
                message="Using keyword-based detection (fallback)"
            )
            self.fallbacks_activated.append("Wake Word Detection")
            
            print("   ⚠️  Porcupine not available")
            print("   ✅ Fallback: Keyword-based wake word detection")
            
            if not porcupine_available:
                self.warnings.append(
                    "Porcupine not installed. Install with: pip install pvporcupine"
                )
                print("   💡 Install Porcupine for better accuracy: pip install pvporcupine")
    
    def _check_ai_service(self, config) -> None:
        """
        Check Ollama and Gemini availability, set up fallback chain.
        
        Requirement: 8.7 - If Ollama unavailable, fallback to Gemini
        """
        print("\n🧠 [2/4] Checking AI Services...")
        
        ollama_available = False
        gemini_available = False
        
        # Check Ollama
        if config.AI_PROVIDER.lower() in ["ollama", "auto"]:
            ollama_available = self._test_ollama_connection(config)
            
            if ollama_available:
                print(f"   ✅ Ollama available at {config.OLLAMA_BASE_URL}")
                print(f"   📦 Model: {config.OLLAMA_MODEL}")
            else:
                print(f"   ⚠️  Ollama not available at {config.OLLAMA_BASE_URL}")
                self.warnings.append(
                    f"Ollama not running. Start with: ollama serve"
                )
                print("   💡 Start Ollama: ollama serve")
                print(f"   💡 Install model: ollama pull {config.OLLAMA_MODEL}")
        
        # Check Gemini
        if config.AI_PROVIDER.lower() in ["gemini", "auto"] or not ollama_available:
            gemini_available = self._test_gemini_connection(config)
            
            if gemini_available:
                print(f"   ✅ Google Gemini available")
                print(f"   📦 Model: {config.AI_MODEL}")
            else:
                print("   ❌ Google Gemini not available (missing/invalid API key)")
                self.errors.append(
                    "Google Gemini API key missing or invalid. "
                    "Get one at: https://aistudio.google.com/app/apikey"
                )
        
        # Determine AI service status
        if config.AI_PROVIDER.lower() == "auto":
            if ollama_available:
                self.components["ai_service"] = ComponentInfo(
                    name="AI Service",
                    status=ComponentStatus.AVAILABLE,
                    message="Ollama (primary) with Gemini fallback"
                )
                print("   🔄 Mode: AUTO - Using Ollama with Gemini fallback")
            elif gemini_available:
                self.components["ai_service"] = ComponentInfo(
                    name="AI Service",
                    status=ComponentStatus.FALLBACK_ACTIVE,
                    fallback_name="Google Gemini",
                    message="Gemini (fallback - Ollama unavailable)"
                )
                self.fallbacks_activated.append("AI Service")
                print("   🔄 Mode: AUTO - Fallback to Gemini (Ollama unavailable)")
            else:
                self.components["ai_service"] = ComponentInfo(
                    name="AI Service",
                    status=ComponentStatus.UNAVAILABLE,
                    message="No AI service available",
                    is_critical=True
                )
                self.errors.append("No AI service available. Cannot start chatbot.")
                print("   ❌ No AI service available!")
        
        elif config.AI_PROVIDER.lower() == "ollama":
            if ollama_available:
                self.components["ai_service"] = ComponentInfo(
                    name="AI Service",
                    status=ComponentStatus.AVAILABLE,
                    message="Ollama local AI"
                )
                print("   ✅ Using Ollama")
            else:
                self.components["ai_service"] = ComponentInfo(
                    name="AI Service",
                    status=ComponentStatus.UNAVAILABLE,
                    message="Ollama not available",
                    is_critical=True
                )
                self.errors.append("Ollama not available. Start with: ollama serve")
                print("   ❌ Ollama not available!")
        
        elif config.AI_PROVIDER.lower() == "gemini":
            if gemini_available:
                self.components["ai_service"] = ComponentInfo(
                    name="AI Service",
                    status=ComponentStatus.AVAILABLE,
                    message="Google Gemini"
                )
                print("   ✅ Using Google Gemini")
            else:
                self.components["ai_service"] = ComponentInfo(
                    name="AI Service",
                    status=ComponentStatus.UNAVAILABLE,
                    message="Gemini not available",
                    is_critical=True
                )
                self.errors.append("Gemini API key missing or invalid")
                print("   ❌ Gemini not available!")
    
    def _check_vb_cable(self, config) -> None:
        """
        Check VB-Cable installation, switch to BASIC_MODE if not found.
        
        Requirement: 17.16 - If VB-Cable not installed, switch to BASIC_MODE
        """
        print("\n🔌 [3/4] Checking VB-Cable (Virtual Audio Cable)...")
        
        vb_cable_installed = self._detect_vb_cable()
        
        if vb_cable_installed:
            self.components["vb_cable"] = ComponentInfo(
                name="VB-Cable",
                status=ComponentStatus.AVAILABLE,
                message="Virtual audio cable detected"
            )
            print("   ✅ VB-Cable detected")
            
            # Check operation mode
            from modules.audio_router import OperationMode
            if config.OPERATION_MODE == OperationMode.FULL_AUTOMATION_MODE.value:
                print("   📍 Operation Mode: FULL_AUTOMATION (using VB-Cable)")
            elif config.OPERATION_MODE == OperationMode.HYBRID_MODE.value:
                print("   📍 Operation Mode: HYBRID (PC + VB-Cable)")
        else:
            self.components["vb_cable"] = ComponentInfo(
                name="VB-Cable",
                status=ComponentStatus.FALLBACK_ACTIVE,
                fallback_name="BASIC_MODE",
                message="Not installed - using BASIC_MODE"
            )
            self.fallbacks_activated.append("Audio Routing")
            
            print("   ⚠️  VB-Cable not detected")
            print("   ✅ Fallback: BASIC_MODE (PC microphone and speakers)")
            
            self.warnings.append(
                "VB-Cable not installed. Install from: https://vb-audio.com/Cable/"
            )
            print("   💡 For camera integration, install VB-Cable from:")
            print("      https://vb-audio.com/Cable/")
            
            # Auto-switch to BASIC_MODE
            from modules.audio_router import OperationMode
            if config.OPERATION_MODE != OperationMode.BASIC_MODE.value:
                print(f"   🔄 Auto-switching: {config.OPERATION_MODE} → BASIC_MODE")
                config.OPERATION_MODE = OperationMode.BASIC_MODE.value
                config.VIRTUAL_CABLE_ENABLED = False
    
    def _check_carecam_sdk(self, config) -> None:
        """
        Check CareCam SDK availability, fallback to UI automation if unavailable.
        
        Requirement: 17.16 - If SDK unavailable, use UI automation (CareCam_Controller)
        """
        print("\n🎥 [4/4] Checking CareCam SDK...")
        
        sdk_available = self._detect_carecam_sdk()
        
        if sdk_available:
            self.components["carecam_sdk"] = ComponentInfo(
                name="CareCam SDK",
                status=ComponentStatus.AVAILABLE,
                message="Native SDK control available"
            )
            print("   ✅ CareCam SDK detected")
            print("   📍 Control Method: Native SDK (programmatic)")
        else:
            self.components["carecam_sdk"] = ComponentInfo(
                name="CareCam SDK",
                status=ComponentStatus.FALLBACK_ACTIVE,
                fallback_name="UI Automation",
                message="SDK not found - using UI automation"
            )
            self.fallbacks_activated.append("Camera Control")
            
            print("   ⚠️  CareCam SDK not detected")
            print("   ✅ Fallback: UI Automation (CareCam_Controller)")
            
            self.warnings.append(
                "CareCam SDK not available. Using UI automation for camera control."
            )
            print("   💡 UI automation uses PyAutoGUI to control camera interface")
    
    def _test_ollama_connection(self, config) -> bool:
        """Test if Ollama is running and model is available"""
        try:
            import ollama
            client = ollama.Client(host=config.OLLAMA_BASE_URL)
            
            # List available models
            models_response = client.list()
            available_models = [model['name'] for model in models_response.get('models', [])]
            
            return config.OLLAMA_MODEL in available_models
        except Exception as e:
            logger.debug(f"Ollama connection test failed: {e}")
            return False
    
    def _test_gemini_connection(self, config) -> bool:
        """Test if Gemini API key is valid"""
        if not config.GOOGLE_API_KEY or config.GOOGLE_API_KEY == "":
            return False
        
        # Don't make actual API call during initialization
        # Just check if key exists and looks valid
        return len(config.GOOGLE_API_KEY) > 10
    
    def _detect_vb_cable(self) -> bool:
        """Detect if VB-Cable is installed"""
        try:
            import pyaudio
            audio = pyaudio.PyAudio()
            
            # Search for VB-Cable devices
            device_count = audio.get_device_count()
            for i in range(device_count):
                try:
                    dev_info = audio.get_device_info_by_index(i)
                    name = dev_info['name'].lower()
                    
                    # Check for VB-Cable keywords
                    if any(keyword in name for keyword in ['cable', 'vb-audio', 'virtual']):
                        audio.terminate()
                        return True
                except Exception:
                    continue
            
            audio.terminate()
            return False
        except Exception as e:
            logger.debug(f"VB-Cable detection failed: {e}")
            return False
    
    def _detect_carecam_sdk(self) -> bool:
        """Detect if CareCam SDK DLL is available"""
        import os
        from modules.carecam_sdk_adapter import CareCamSDKAdapter
        
        sdk_path = CareCamSDKAdapter.DEFAULT_SDK_PATH
        return os.path.exists(sdk_path)
    
    def _display_initialization_summary(self) -> None:
        """Display initialization summary"""
        print("\n" + "=" * 70)
        print("📋 Initialization Summary")
        print("=" * 70)
        
        # Display component statuses
        for component_name, component_info in self.components.items():
            status_icon = {
                ComponentStatus.AVAILABLE: "✅",
                ComponentStatus.FALLBACK_ACTIVE: "🔄",
                ComponentStatus.UNAVAILABLE: "❌",
                ComponentStatus.NOT_CHECKED: "❔"
            }[component_info.status]
            
            print(f"\n{status_icon} {component_info.name}")
            print(f"   Status: {component_info.status.value}")
            print(f"   {component_info.message}")
            
            if component_info.fallback_name:
                print(f"   Fallback: {component_info.fallback_name}")
        
        # Display fallbacks activated
        if self.fallbacks_activated:
            print(f"\n🔄 Fallbacks Activated: {len(self.fallbacks_activated)}")
            for fallback in self.fallbacks_activated:
                print(f"   - {fallback}")
        
        # Display warnings
        if self.warnings:
            print(f"\n⚠️  Warnings: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"   - {warning}")
        
        # Display errors
        if self.errors:
            print(f"\n❌ Errors: {len(self.errors)}")
            for error in self.errors:
                print(f"   - {error}")
        
        print("\n" + "=" * 70)
    
    def _can_start_system(self) -> bool:
        """
        Determine if system can start based on component availability.
        
        Returns:
            True if system can start (all critical components available)
        """
        # Check for critical component failures
        for component_info in self.components.values():
            if component_info.is_critical and component_info.status == ComponentStatus.UNAVAILABLE:
                print("\n❌ Cannot start system: Critical component unavailable")
                return False
        
        print("\n✅ System ready to start")
        return True
    
    def get_status_report(self) -> str:
        """
        Get human-readable status report.
        
        Returns:
            Status report string
        """
        lines = []
        lines.append("=== Tỷ Tỷ Chatbot System Status ===")
        lines.append("")
        
        for component_name, component_info in self.components.items():
            status_str = component_info.status.value.upper()
            lines.append(f"{component_info.name}: {status_str}")
            lines.append(f"  {component_info.message}")
            
            if component_info.fallback_name:
                lines.append(f"  Fallback: {component_info.fallback_name}")
            
            lines.append("")
        
        if self.fallbacks_activated:
            lines.append(f"Fallbacks Active: {', '.join(self.fallbacks_activated)}")
        
        if self.warnings:
            lines.append("")
            lines.append("Warnings:")
            for warning in self.warnings:
                lines.append(f"  - {warning}")
        
        if self.errors:
            lines.append("")
            lines.append("Errors:")
            for error in self.errors:
                lines.append(f"  - {error}")
        
        return "\n".join(lines)


def initialize_system_with_fallbacks(config):
    """
    Convenience function to initialize system with fallback detection.
    
    Args:
        config: System configuration object
        
    Returns:
        SystemStatus object
    """
    initializer = SystemInitializer()
    return initializer.initialize_system(config)


# Module test
if __name__ == "__main__":
    """Test system initializer"""
    import sys
    import os
    
    # Add parent directory to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from config import config
    
    print("Testing System Initializer with Graceful Degradation\n")
    
    # Initialize system
    status = initialize_system_with_fallbacks(config)
    
    # Display results
    print("\n" + "=" * 70)
    print("📊 Initialization Results")
    print("=" * 70)
    print(f"\nSystem Initialized: {status.initialized}")
    print(f"Components Checked: {len(status.components)}")
    print(f"Fallbacks Activated: {len(status.fallbacks_activated)}")
    print(f"Warnings: {len(status.warnings)}")
    print(f"Errors: {len(status.errors)}")
    
    if status.initialized:
        print("\n✅ System is ready to start!")
    else:
        print("\n❌ System cannot start due to critical errors")
    
    # Display detailed report
    print("\n" + "=" * 70)
    print("📋 Detailed Status Report")
    print("=" * 70)
    print()
    
    initializer = SystemInitializer()
    initializer.components = status.components
    initializer.fallbacks_activated = status.fallbacks_activated
    initializer.warnings = status.warnings
    initializer.errors = status.errors
    
    print(initializer.get_status_report())
