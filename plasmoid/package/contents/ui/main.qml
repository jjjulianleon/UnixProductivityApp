import QtQuick 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls 2.15
import org.kde.plasma.components 3.0 as PlasmaComponents
import org.kde.plasma.plasma5support as Plasma5Support
import org.kde.plasma.plasmoid 2.0
import org.kde.plasma.core 2.0 as PlasmaCore

PlasmoidItem {
    id: root
    
    // Enable translucency
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    
    // Theme Colors
    // Adaptive default: 0.3 on desktop (Glass), 0.0 in panel (Transparent to let Panel style show)
    // FORCE TRANSPARENT FOR DEBUGGING PANEL ISSUE
    readonly property double defaultOpacity: 0.0
    readonly property color cBgWindow: Qt.rgba(0.1, 0.1, 0.1, 0.0) 
    readonly property color cBgCard: Qt.rgba(1, 1, 1, 0.08)
    readonly property color cAccent: "#4285f4" // Blue
    readonly property color cUrgent: "#ea4335" // Red
    readonly property color cWarning: "#fbbc05" // Yellow
    readonly property color cSuccess: "#34a853" // Green
    
    // Data source for launching app
    Plasma5Support.DataSource {
        id: appLauncher
        engine: "executable"
        connectedSources: []
        onNewData: {
             // We don't care about output, just execution
             disconnectSource(sourceName) // Run once
        }
    }
    
    // Data source 
    Plasma5Support.DataSource {
        id: pySource
        engine: "executable"
        connectedSources: []
        onNewData: {
            var output = data["stdout"]
            if (output) {
                try {
                    var json = JSON.parse(output)
                    updateUI(json)
                } catch (e) { }
            }
        }
    }
    
    function refreshData(sync) {
        if (sync) isSyncing = true
        var cmd = "python3 /home/jjulianleon/.local/share/unix-productivity/plasmoid_backend.py"
        if (sync) cmd += " --sync"
        pySource.connectedSources = [cmd]
    }
    
    Timer {
        interval: 5000; running: true; repeat: true; onTriggered: refreshData(false)
        triggeredOnStart: true
    }
    
    Component.onCompleted: {
        generateCalendar()
        refreshData(false)
    }
    
    // Models
    property var stats: {"pending":0, "today":0, "overdue":0, "completed":0}
    property var urgentTask: null
    property var nextClass: null
    property var calendarDays: []
    property var calendarEvents: ({})
    property string currentFont: ""
    
    // Pomodoro
    property bool pomodoroRunning: false
    property int pomodoroSeconds: 1500
    property bool isBreak: false
    property bool isSyncing: false
    
    function generateCalendar() {
        var d = new Date()
        var year = d.getFullYear()
        var month = d.getMonth()
        var firstDay = new Date(year, month, 1)
        var lastDay = new Date(year, month + 1, 0)
        
        var startDay = firstDay.getDay()
        if (startDay === 0) startDay = 7
        startDay -= 1 
        
        var days = []
        for (var i=0; i < startDay; i++) days.push(0)
        for (var k=1; k <= lastDay.getDate(); k++) days.push(k)
        calendarDays = days
    }

    function updateUI(data) {
        isSyncing = false
        // Always update stats to ensure synchronization
        stats = data.stats
        
        // Always update other simple objects
        urgentTask = data.urgent
        nextClass = data.next_class
        
        // Optimize calendar events (heavy)
        var newEvents = JSON.stringify(data.calendar_events || {})
        if (JSON.stringify(calendarEvents) !== newEvents) {
            calendarEvents = data.calendar_events || {}
        }
        
        if (data.font && data.font !== currentFont) currentFont = data.font
    }

    Timer {
        interval: 1000; running: pomodoroRunning; repeat: true
        onTriggered: {
            if (pomodoroSeconds > 0) pomodoroSeconds--
            else {
                pomodoroRunning = false
                isBreak = !isBreak
                pomodoroSeconds = isBreak ? 300 : 1500
            }
        }
    }
    
    // --- MAIN UI ---
    Rectangle {
        anchors.fill: parent
        color: cBgWindow
        radius: 12
        
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 12
            
            // TOP BAR
            RowLayout {
                Layout.fillWidth: true
                PlasmaComponents.Label {
                    text: Qt.formatDateTime(new Date(), "ddd dd/MM hh:mm")
                    font.pixelSize: 13
                    font.family: root.currentFont != "" ? root.currentFont : undefined
                    color: "white"
                    opacity: 0.8
                }
                Item { Layout.fillWidth: true }
                
                // Sync Button
                Rectangle {
                    Layout.preferredWidth: 90
                    Layout.preferredHeight: 28
                    color: isSyncing ? Qt.rgba(0.2, 0.8, 0.2, 0.4) : Qt.rgba(1, 1, 1, 0.1)
                    radius: 14
                    
                    PlasmaComponents.Label {
                        anchors.centerIn: parent
                        text: isSyncing ? "Sincronizando..." : "Sincronizar"
                        color: "white"
                        font.family: root.currentFont != "" ? root.currentFont : undefined
                        font.pixelSize: 11
                        font.bold: true
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: refreshData(true)
                        enabled: !isSyncing
                        hoverEnabled: true
                        onEntered: if (!isSyncing) parent.color = Qt.rgba(1, 1, 1, 0.2)
                        onExited: if (!isSyncing) parent.color = Qt.rgba(1, 1, 1, 0.1)
                    }
                }
                
                // Open App Button
                Rectangle {
                    Layout.preferredWidth: 90
                    Layout.preferredHeight: 28
                    color: Qt.rgba(0.26, 0.52, 0.96, 0.2) // More translucent
                    radius: 14
                    
                    PlasmaComponents.Label {
                        anchors.centerIn: parent
                        text: "Abrir App"
                        color: "white"
                        font.family: root.currentFont != "" ? root.currentFont : undefined
                        font.pixelSize: 11
                        font.bold: true
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            appLauncher.connectedSources = [] 
                            // Use gio launch to run the installed .desktop file (more robust than gtk-launch)
                            appLauncher.connectedSources = ["gio launch /home/jjulianleon/.local/share/applications/unix-productivity.desktop"]
                        }
                        hoverEnabled: true
                        onEntered: parent.color = Qt.rgba(0.26, 0.52, 0.96, 0.6)
                        onExited: parent.color = Qt.rgba(0.26, 0.52, 0.96, 0.4)
                    }
                }
            }
            
            // STATS ROW
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                StatCard { value: stats.pending; label: "pendientes"; textColor: cAccent }
                StatCard { value: stats.today; label: "hoy"; textColor: cWarning }
                StatCard { value: stats.overdue; label: "atrasadas"; textColor: cUrgent }
                StatCard { value: stats.completed; label: "listas"; textColor: cSuccess }
            }
            
            // CONTENT ROW
            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 12
                
                // LEFT: Calendar
                ColumnLayout {
                    Layout.fillHeight: true
                                        Layout.preferredWidth: parent.width * 0.55
                                        spacing: 12
                                        
                                        Rectangle {
                                            Layout.fillWidth: true
                                            Layout.fillHeight: true
                                            Layout.minimumHeight: 150 // Prevent collapse
                                            color: cBgCard
                                            radius: 10
                    
                    
                        
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 4
                            
                            PlasmaComponents.Label {
                                Layout.alignment: Qt.AlignHCenter
                                text: Qt.formatDateTime(new Date(), "MMMM yyyy")
                                font.bold: true
                                font.family: root.currentFont != "" ? root.currentFont : undefined
                                color: "white"
                            }
                            
                            GridLayout {
                                columns: 7
                                Layout.fillWidth: true
                                columnSpacing: 4
                                RowLayout { Layout.columnSpan: 7; spacing: 0 
                                    Repeater { model: ["L","M","X","J","V","S","D"]; PlasmaComponents.Label { text: modelData; Layout.fillWidth: true; horizontalAlignment: Text.AlignHCenter; font.pixelSize: 10; font.family: root.currentFont != "" ? root.currentFont : undefined; color: "white"; opacity: 0.5 } }
                                }
                                
                                Repeater {
                                    model: calendarDays
                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true // Fill cell
                                        color: (modelData > 0 && modelData === new Date().getDate()) ? Qt.rgba(0.26, 0.52, 0.96, 0.5) : "transparent"
                                        radius: 6 // Softer radius
                                        visible: true
                                        
                                        property string dateKey: {
                                            if (modelData <= 0) return ""
                                            var d = new Date()
                                            var m = d.getMonth() + 1
                                            return d.getFullYear() + "-" + (m<10?"0"+m:m) + "-" + (modelData<10?"0"+modelData:modelData)
                                        }
                                        property var dayEvents: calendarEvents[dateKey] || []
                                        
                                        PlasmaComponents.Label {
                                            anchors.centerIn: parent
                                            text: modelData > 0 ? modelData : ""
                                            color: "white"
                                            font.pixelSize: 11
                                            font.family: root.currentFont != "" ? root.currentFont : undefined
                                            opacity: modelData > 0 ? (dayEvents.length > 0 ? 1 : 0.9) : 0
                                            font.bold: dayEvents.length > 0
                                        }
                                        
                                        // Red Dot for Events
                                        Rectangle {
                                            width: 4; height: 4; radius: 2
                                            color: cUrgent
                                            anchors.bottom: parent.bottom
                                            anchors.horizontalCenter: parent.horizontalCenter
                                            anchors.bottomMargin: 2
                                            visible: dayEvents.length > 0
                                        }
                                        
                                        // Tooltip / Popup on Hover/Click
                                        MouseArea {
                                            anchors.fill: parent
                                            enabled: dayEvents.length > 0
                                            hoverEnabled: true
                                            onClicked: {
                                                if (dayEvents.length > 0) {
                                                    print("Eventos: " + dayEvents.join(", "))
                                                    // Simple overlay or tooltip could go here
                                                }
                                            }
                                            PlasmaComponents.ToolTip.visible: containsMouse
                                            PlasmaComponents.ToolTip.text: dayEvents.join("\n")
                                            PlasmaComponents.ToolTip.delay: 0
                                        }
                                    }
                                }
                            }
                            Item { Layout.fillHeight: true }
                        }
                    }
                    
                    // Next Class
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 50
                        Layout.minimumHeight: 50
                        color: Qt.rgba(0.26, 0.52, 0.96, 0.15)
                        radius: 8
                        
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 8
                            spacing: 0
                            PlasmaComponents.Label { text: "Próxima clase"; font.pixelSize: 10; font.family: root.currentFont != "" ? root.currentFont : undefined; opacity: 0.7; color: "white" }
                            RowLayout {
                                spacing: 6
                                PlasmaComponents.Label { 
                                    text: nextClass ? nextClass.name : "Sin más clases"
                                    font.bold: true
                                    font.pixelSize: 12
                                    font.family: root.currentFont != "" ? root.currentFont : undefined
                                    color: "white"
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }
                                PlasmaComponents.Label { 
                                    text: nextClass ? "en " + nextClass.minutes + " min" : "hoy"
                                    font.pixelSize: 11
                                    font.family: root.currentFont != "" ? root.currentFont : undefined
                                    opacity: 0.8
                                    color: "white"
                                }
                            }
                        }
                    }
                }
                
                // RIGHT: Urgent & Pomodoro
                ColumnLayout {
                    Layout.fillHeight: true
                    Layout.preferredWidth: parent.width * 0.45
                    spacing: 12
                    
                    // Urgent
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 65
                        color: Qt.rgba(0.91, 0.26, 0.2, 0.15)
                        radius: 8
                        
                        Rectangle {
                            width: 3; height: 30
                            color: cUrgent
                            anchors.left: parent.left; anchors.verticalCenter: parent.verticalCenter
                            anchors.leftMargin: 4
                            radius: 2
                        }
                        
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            anchors.leftMargin: 16
                            spacing: 2
                            
                            PlasmaComponents.Label { text: "⚠ Urgente"; color: "#ff8a80"; font.pixelSize: 10; font.family: root.currentFont != "" ? root.currentFont : undefined; font.bold: true }
                            PlasmaComponents.Label { 
                                text: urgentTask ? urgentTask.title : "Nada pendiente"
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                                font.bold: true
                                font.pixelSize: 12
                                font.family: root.currentFont != "" ? root.currentFont : undefined
                                color: "white"
                            }
                            PlasmaComponents.Label { 
                                text: urgentTask ? (urgentTask.days_left < 0 ? "¡Atrasado!" : "En " + urgentTask.days_left + " días") : ""
                                font.pixelSize: 10
                                font.family: root.currentFont != "" ? root.currentFont : undefined
                                opacity: 0.8
                                color: "white"
                            }
                        }
                    }
                    
                    // Pomodoro
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        color: cBgCard
                        radius: 10
                        
                        ColumnLayout {
                            anchors.centerIn: parent
                            spacing: 8
                            
                            PlasmaComponents.Label { 
                                text: isBreak ? "Descanso" : "Pomodoro"
                                opacity: 0.5 
                                font.pixelSize: 11
                                font.family: root.currentFont != "" ? root.currentFont : undefined
                                Layout.alignment: Qt.AlignHCenter
                                color: "white"
                            }
                            
                            PlasmaComponents.Label { 
                                text: {
                                    var m = Math.floor(pomodoroSeconds / 60)
                                    var s = pomodoroSeconds % 60
                                    return (m < 10 ? "0"+m : m) + ":" + (s < 10 ? "0"+s : s)
                                }
                                font.pixelSize: 28
                                font.family: root.currentFont != "" ? root.currentFont : undefined
                                font.bold: true
                                Layout.alignment: Qt.AlignHCenter
                                color: "white"
                            }
                            
                            RowLayout {
                                Layout.alignment: Qt.AlignHCenter
                                spacing: 12
                                
                                // Play (Text Icon)
                                Rectangle {
                                    width: 36; height: 36; radius: 18
                                    color: Qt.rgba(0.26, 0.52, 0.96, 0.25) // More translucent
                                    
                                    Text {
                                        anchors.centerIn: parent
                                        text: pomodoroRunning ? "⏸" : "▶"
                                        color: "white"
                                        font.pixelSize: 14
                                    }
                                    MouseArea {
                                        anchors.fill: parent
                                        onClicked: pomodoroRunning = !pomodoroRunning
                                        hoverEnabled: true
                                        onEntered: parent.color = Qt.rgba(0.26, 0.52, 0.96, 0.7)
                                        onExited: parent.color = Qt.rgba(0.26, 0.52, 0.96, 0.5)
                                    }
                                }
                                
                                // Reset (Text Icon)
                                Rectangle {
                                    width: 36; height: 36; radius: 18
                                    color: "transparent"
                                    border.color: Qt.rgba(1,1,1,0.2); border.width: 1
                                    
                                    Text {
                                        anchors.centerIn: parent
                                        text: "↻"
                                        color: "white"
                                        font.pixelSize: 18
                                        opacity: 0.8
                                    }
                                    MouseArea {
                                        anchors.fill: parent
                                        onClicked: { pomodoroRunning = false; pomodoroSeconds = 1500; isBreak = false }
                                        hoverEnabled: true
                                        onEntered: parent.border.color = Qt.rgba(1,1,1,0.5)
                                        onExited: parent.border.color = Qt.rgba(1,1,1,0.2)
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    // Fixed StatCard
    component StatCard : Rectangle {
        property int value: 0
        property string label: ""
        property color textColor: "white" // Fixed name
        
        Layout.fillWidth: true
        Layout.preferredHeight: 50
        color: cBgCard
        radius: 8
        
        ColumnLayout {
            anchors.centerIn: parent
            spacing: 0
            PlasmaComponents.Label {
                text: value
                font.bold: true
                font.pixelSize: 18
                font.family: root.currentFont != "" ? root.currentFont : undefined
                color: textColor // Usage
                Layout.alignment: Qt.AlignHCenter
            }
            PlasmaComponents.Label {
                text: label
                font.pixelSize: 10
                font.family: root.currentFont != "" ? root.currentFont : undefined
                opacity: 0.6
                Layout.alignment: Qt.AlignHCenter
                color: "white"
            }
        }
    }
}
