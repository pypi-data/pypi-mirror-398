"""GUI components for pressure visualization with controls."""

import sys
import traceback
import time
import os
from Cocoa import (NSApplication, NSView, NSWindow, NSRect, NSColor, 
                   NSEvent, NSFont, NSAttributedString, NSButton, NSTextField)
from AppKit import (NSFontAttributeName, NSForegroundColorAttributeName, NSRectFill,
                   NSCenterTextAlignment)
from PyObjCTools import AppHelper

def log_error(message, error=None):
    """Log errors to stderr."""
    print(f"ERROR: {message}", file=sys.stderr, flush=True)
    if error:
        print(f"  Exception: {error}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)

class PressureView(NSView):
    """View for displaying pressure values with controls."""
    
    def initWithFrame_monitor_(self, frame, monitor=None):
        self = NSView.initWithFrame_(self, frame)
        if self:
            self.monitor = monitor
            self.currentPressure = 0.0
            self.maxPressure = 0.0
            self.minPressure = 1.0
            self.sampleCount = 0
            self.isRecording = False
            self.recordedData = []  # Store all recorded pressure samples
            # Add control buttons (after view is initialized)
        return self
    
    def viewDidMoveToWindow(self):
        """Called when view is added to window."""
        try:
            self.window().makeFirstResponder_(self)
            # Setup controls after view is in window
            self.setupControls()
        except Exception as e:
            log_error("Failed in viewDidMoveToWindow", e)
    
    def setupControls(self):
        """Setup control buttons and labels."""
        try:
            bounds = self.bounds()
            
            # Record button (top left area)
            self.recordButton = NSButton.alloc().initWithFrame_(
                NSRect((20, bounds.size.height - 60), (140, 32))
            )
            self.recordButton.setButtonType_(0)  # NSMomentaryLightButton
            self.recordButton.setBezelStyle_(1)  # NSRoundedBezelStyle
            self.recordButton.setTitle_("▶ Start Recording")
            self.recordButton.setFont_(NSFont.systemFontOfSize_(13))
            self.recordButton.setTarget_(self)
            self.recordButton.setAction_("toggleRecording:")
            self.addSubview_(self.recordButton)
            
            # Reset button (next to record)
            self.resetButton = NSButton.alloc().initWithFrame_(
                NSRect((170, bounds.size.height - 60), (120, 32))
            )
            self.resetButton.setButtonType_(0)  # NSMomentaryLightButton
            self.resetButton.setBezelStyle_(1)  # NSRoundedBezelStyle
            self.resetButton.setTitle_("↻ Reset Stats")
            self.resetButton.setFont_(NSFont.systemFontOfSize_(13))
            self.resetButton.setTarget_(self)
            self.resetButton.setAction_("resetStats:")
            self.addSubview_(self.resetButton)
            
            # Export CSV button
            self.exportButton = NSButton.alloc().initWithFrame_(
                NSRect((300, bounds.size.height - 60), (120, 32))
            )
            self.exportButton.setButtonType_(0)  # NSMomentaryLightButton
            self.exportButton.setBezelStyle_(1)  # NSRoundedBezelStyle
            self.exportButton.setTitle_("💾 Export CSV")
            self.exportButton.setFont_(NSFont.systemFontOfSize_(13))
            self.exportButton.setTarget_(self)
            self.exportButton.setAction_("exportCSV:")
            self.addSubview_(self.exportButton)
            
            # Stats panel background
            self.statsPanel = NSView.alloc().initWithFrame_(
                NSRect((bounds.size.width - 200, 20), (180, 140))
            )
            self.statsPanel.setWantsLayer_(True)
            self.statsPanel.layer().setBackgroundColor_(
                NSColor.colorWithRed_green_blue_alpha_(0.95, 0.95, 0.95, 1.0).CGColor()
            )
            self.statsPanel.layer().setCornerRadius_(10.0)
            self.addSubview_(self.statsPanel)
            
            # Stats title
            self.statsTitleLabel = NSTextField.alloc().initWithFrame_(
                NSRect((10, 110), (160, 20))
            )
            self.statsTitleLabel.setEditable_(False)
            self.statsTitleLabel.setBordered_(False)
            self.statsTitleLabel.setDrawsBackground_(False)
            self.statsTitleLabel.setTextColor_(NSColor.blackColor())
            self.statsTitleLabel.setFont_(NSFont.boldSystemFontOfSize_(12))
            self.statsTitleLabel.setStringValue_("📊 STATISTICS")
            self.statsTitleLabel.setAlignment_(NSCenterTextAlignment)
            self.statsPanel.addSubview_(self.statsTitleLabel)
            
            # Stats label
            self.statsLabel = NSTextField.alloc().initWithFrame_(
                NSRect((10, 10), (160, 95))
            )
            self.statsLabel.setEditable_(False)
            self.statsLabel.setBordered_(False)
            self.statsLabel.setDrawsBackground_(False)
            self.statsLabel.setTextColor_(NSColor.darkGrayColor())
            self.statsLabel.setFont_(NSFont.monospacedSystemFontOfSize_weight_(11, 0))
            self.statsLabel.setStringValue_("Samples: 0\nCurrent: 0.000\nMin: ---\nMax: ---")
            self.statsPanel.addSubview_(self.statsLabel)
            
        except Exception as e:
            log_error("Failed to setup controls", e)
    
    def toggleRecording_(self, sender):
        """Toggle recording state."""
        self.isRecording = not self.isRecording
        if self.isRecording:
            self.recordButton.setTitle_("■ Stop Recording")
            self.recordingStartTime = time.time()
            print("Started recording pressure data...")
        else:
            self.recordButton.setTitle_("▶ Start Recording")
            print(f"Stopped recording. Collected {self.sampleCount} samples.")
            if self.recordedData:
                print(f"Click 'Export CSV' to save the data.")
        self.setNeedsDisplay_(True)
    
    def resetStats_(self, sender):
        """Reset statistics."""
        self.maxPressure = 0.0
        self.minPressure = 1.0
        self.sampleCount = 0
        self.recordedData = []
        self.isRecording = False
        self.recordButton.setTitle_("▶ Start Recording")
        self.updateStatsLabel()
        self.setNeedsDisplay_(True)
        print("Statistics reset.")
    
    def exportCSV_(self, sender):
        """Export recorded data to CSV."""
        if not self.recordedData:
            print("No data to export. Start recording first!")
            return
        
        try:
            # Create filename with timestamp
            timestamp = int(time.time())
            filename = f"pressure_data_{timestamp}.csv"
            filepath = os.path.expanduser(f"~/Desktop/{filename}")
            
            # Write CSV manually (no pandas dependency in main package)
            with open(filepath, 'w') as f:
                f.write("timestamp,pressure,stage\n")
                for row in self.recordedData:
                    f.write(f"{row['timestamp']:.3f},{row['pressure']:.3f},{row['stage']}\n")
            
            print(f"✓ Exported {len(self.recordedData)} samples to: {filepath}")
            print(f"  File saved to Desktop: {filename}")
            
        except Exception as e:
            print(f"Error exporting CSV: {e}", file=sys.stderr)
    
    def updateStatsLabel(self):
        """Update statistics label."""
        if self.sampleCount > 0:
            stats_text = (f"Samples: {self.sampleCount}\n"
                         f"Current: {self.currentPressure:.3f}\n"
                         f"Min: {self.minPressure:.3f}\n"
                         f"Max: {self.maxPressure:.3f}")
        else:
            stats_text = "Samples: 0\nCurrent: 0.000\nMin: ---\nMax: ---"
        
        self.statsLabel.setStringValue_(stats_text)
    
    def acceptsFirstResponder(self):
        return True
    
    def drawRect_(self, rect):
        """Draw the pressure value on the view."""
        try:
            # White background
            NSColor.whiteColor().setFill()
            NSRectFill(rect)
            
            bounds = self.bounds()
            
            # Draw title at top
            titleFont = NSFont.boldSystemFontOfSize_(18.0)
            titleAttributes = {
                NSFontAttributeName: titleFont,
                NSForegroundColorAttributeName: NSColor.darkGrayColor()
            }
            titleStr = "TRACKPAD PRESSURE MONITOR"
            titleAttributedString = NSAttributedString.alloc().initWithString_attributes_(
                titleStr, titleAttributes
            )
            titleSize = titleAttributedString.size()
            titleX = (bounds.size.width - titleSize.width) / 2.0
            titleY = bounds.size.height - 35
            titleAttributedString.drawAtPoint_((titleX, titleY))
            
            # Draw large pressure value in center
            font = NSFont.monospacedSystemFontOfSize_weight_(96.0, 0.3)
            
            # Color based on pressure
            if self.currentPressure > 0.7:
                textColor = NSColor.colorWithRed_green_blue_alpha_(0.8, 0.2, 0.2, 1.0)
            elif self.currentPressure > 0.4:
                textColor = NSColor.colorWithRed_green_blue_alpha_(0.2, 0.5, 0.8, 1.0)
            else:
                textColor = NSColor.colorWithRed_green_blue_alpha_(0.3, 0.3, 0.3, 1.0)
            
            attributes = {
                NSFontAttributeName: font,
                NSForegroundColorAttributeName: textColor
            }
            
            pressureStr = f"{self.currentPressure:.3f}"
            attributedString = NSAttributedString.alloc().initWithString_attributes_(
                pressureStr, attributes
            )
            
            textSize = attributedString.size()
            x = (bounds.size.width - textSize.width) / 2.0
            y = (bounds.size.height - textSize.height) / 2.0
            
            attributedString.drawAtPoint_((x, y))
            
            # Draw instruction label below pressure
            labelFont = NSFont.systemFontOfSize_(14.0)
            labelAttributes = {
                NSFontAttributeName: labelFont,
                NSForegroundColorAttributeName: NSColor.grayColor()
            }
            labelStr = "Press on trackpad with varying pressure"
            labelAttributedString = NSAttributedString.alloc().initWithString_attributes_(
                labelStr, labelAttributes
            )
            labelSize = labelAttributedString.size()
            labelX = (bounds.size.width - labelSize.width) / 2.0
            labelY = y - 35
            labelAttributedString.drawAtPoint_((labelX, labelY))
            
            # Draw recording indicator
            if self.isRecording:
                recordFont = NSFont.boldSystemFontOfSize_(14.0)
                recordAttributes = {
                    NSFontAttributeName: recordFont,
                    NSForegroundColorAttributeName: NSColor.redColor()
                }
                recordStr = "● RECORDING"
                recordAttributedString = NSAttributedString.alloc().initWithString_attributes_(
                    recordStr, recordAttributes
                )
                recordSize = recordAttributedString.size()
                recordX = (bounds.size.width - recordSize.width) / 2.0
                recordY = labelY - 30
                recordAttributedString.drawAtPoint_((recordX, recordY))
            
        except Exception as e:
            log_error("Failed to draw pressure value", e)
    
    def updatePressure_(self, pressure):
        """Update pressure value and redraw."""
        self.currentPressure = pressure
        
        # Update statistics only when recording
        if self.isRecording:
            self.sampleCount += 1
            if pressure > self.maxPressure:
                self.maxPressure = pressure
            if pressure < self.minPressure and pressure > 0:
                self.minPressure = pressure
            
            # Store the data point with timestamp
            if not hasattr(self, 'recordingStartTime'):
                self.recordingStartTime = time.time()
            
            self.recordedData.append({
                'timestamp': time.time() - self.recordingStartTime,
                'pressure': pressure,
                'stage': 0  # Will be updated from event
            })
            
            self.updateStatsLabel()
        
        self.setNeedsDisplay_(True)

    def pressureChangeWithEvent_(self, event):
        """Handle pressure events from Force Touch trackpad."""
        try:
            pressure = event.pressure()
            # Don't try to get stage - it causes assertion failures
            # Stage info is not reliable for all event types
            stage = 0
            
            # Update the last recorded data point
            if self.isRecording and self.recordedData:
                self.recordedData[-1]['stage'] = stage
            
            self.updatePressure_(pressure)
            
            if self.monitor:
                # Pass a simplified event to monitor
                if self.monitor.callback:
                    self.monitor.callback(pressure, stage)
            else:
                if self.isRecording:
                    print(f"Pressure: {pressure:.3f}", flush=True)
                
        except Exception as e:
            log_error("Failed to get pressure in pressureChangeWithEvent", e)

    def mouseDown_(self, event):
        """Handle mouse down events."""
        try:
            if hasattr(event, 'pressure'):
                pressure = event.pressure()
                self.updatePressure_(pressure)
                
                if self.monitor and self.monitor.callback:
                    self.monitor.callback(pressure, 0)
                    
        except Exception as e:
            log_error("Failed to get pressure in mouseDown", e)

    def mouseDragged_(self, event):
        """Handle mouse drag events."""
        try:
            if hasattr(event, 'pressure'):
                pressure = event.pressure()
                self.updatePressure_(pressure)
                
                if self.monitor and self.monitor.callback:
                    self.monitor.callback(pressure, 0)
                    
        except Exception as e:
            log_error("Failed to get pressure in mouseDragged", e)

def start_gui_monitor(monitor=None):
    """
    Start the GUI pressure monitor with controls.
    
    Args:
        monitor: Optional PressureMonitor instance for callbacks
    """
    try:
        app = NSApplication.sharedApplication()
        app.setActivationPolicy_(0)
        
        # Larger window to accommodate controls
        window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSRect((100, 100), (700, 450)),
            15,
            2,
            False
        )
        
        window.setTitle_("Trackpad Pressure Monitor")
        window.setBackgroundColor_(NSColor.whiteColor())
        
        view = PressureView.alloc().initWithFrame_monitor_(
            window.contentView().frame(), monitor
        )
        window.setContentView_(view)
        window.makeKeyAndOrderFront_(None)
        
        app.activateIgnoringOtherApps_(True)
        print("Pressure monitor started with controls.")
        print("- Click 'Start Recording' to begin collecting statistics")
        print("- Click 'Reset Stats' to clear data")
        print("- Press on the trackpad to see values\n")
        AppHelper.runEventLoop()
        
    except Exception as e:
        log_error("Failed to start GUI monitor", e)
        sys.exit(1)