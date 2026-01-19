import QtQuick 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls 2.15
import org.kde.plasma.components 3.0 as PlasmaComponents
import org.kde.plasma.core 2.0 as PlasmaCore
import org.kde.plasma.plasmoid 2.0

Item {
    id: root
    
    // Data source from Python script
    PlasmaCore.DataSource {
        id: pySource
        engine: "executable"
        connectedSources: []
        onNewData: {
            var output = data["stdout"]
            if (output) {
                try {
                    var json = JSON.parse(output)
                    updateUI(json)
                } catch (e) {
                    console.error("JSON Error: " + e)
                }
            }
        }
    }
    
    function refreshData() {
        pySource.connectedSources = ["python3 /home/jjulianleon/.local/share/unix-productivity/plasmoid_backend.py"]
    }
    
    Timer {
        interval: 5000 // Refresh every 5s
        running: true
        repeat: true
        onTriggered: refreshData()
    }
    
    Component.onCompleted: refreshData()
    
    // Properties
    property var stats: {"pending":0, "today":0, "overdue":0, "completed":0}
    property var urgentTask: null
    property var nextClass: null
    property bool pomodoroRunning: false
    property int pomodoroSeconds: 1500
    
    function updateUI(data) {
        stats = data.stats
        urgentTask = data.urgent
        nextClass = data.next_class
    }

    // Pomodoro Timer
    Timer {
        id: pomoTimer
        interval: 1000
        running: pomodoroRunning
        repeat: true
        onTriggered: {
            if (pomodoroSeconds > 0) {
                pomodoroSeconds--
            } else {
                pomodoroRunning = false
                pomodoroSeconds = 1500 // Reset to 25m
            }
        }
    }
    
    // Main UI
    ColumnLayout {
        anchors.fill: parent
        spacing: 8
        
        // Top Bar
        RowLayout {
            Layout.fillWidth: true
            PlasmaComponents.Label {
                text: Qt.formatDateTime(new Date(), "ddd dd/MM hh:mm")
                opacity: 0.7
            }
            Item { Layout.fillWidth: true }
            PlasmaComponents.Button {
                text: "Abrir App"
                icon.name: "unix-productivity"
                onClicked: {
                    Qt.openUrlExternally("file:///home/jjulianleon/.local/bin/unix-productivity")
                }
            }
        }
        
        // Stats Row
        RowLayout {
            Layout.fillWidth: true
            spacing: 4
            
            StatCard { value: stats.pending; label: "pendientes"; color: "#4285f4" }
            StatCard { value: stats.today; label: "hoy"; color: "#fbbc05" }
            StatCard { value: stats.overdue; label: "atrasadas"; color: "#ea4335" }
            StatCard { value: stats.completed; label: "listas"; color: "#34a853" }
        }
        
        // Content Area
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 8
            
            // Left Col (Calendar Placeholder + Next Class)
            ColumnLayout {
                Layout.fillHeight: true
                Layout.preferredWidth: parent.width * 0.6
                
                // Calendar Grid (Simplified)
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: Qt.rgba(1,1,1,0.1)
                    radius: 8
                    
                    ColumnLayout {
                        anchors.centerIn: parent
                        PlasmaComponents.Label { 
                            text: Qt.formatDateTime(new Date(), "MMMM yyyy") 
                            font.bold: true
                            Layout.alignment: Qt.AlignHCenter
                        }
                        // Grid would go here
                        PlasmaComponents.Label { 
                            text: "(Calendario)" 
                            opacity: 0.5 
                            Layout.alignment: Qt.AlignHCenter
                        }
                    }
                }
                
                // Next Class Card
                Rectangle {
                    Layout.fillWidth: true
                    height: 50
                    color: Qt.rgba(0.2, 0.6, 1, 0.15)
                    radius: 8
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 8
                        PlasmaComponents.Label { 
                            text: "Próxima clase"
                            font.pixelSize: 10
                            opacity: 0.7
                        }
                        PlasmaComponents.Label { 
                            text: nextClass ? nextClass.name : "Sin más clases"
                            font.bold: true
                        }
                        PlasmaComponents.Label { 
                            text: nextClass ? "en " + nextClass.minutes + " min" : "hoy"
                            font.pixelSize: 10
                            visible: !!nextClass
                        }
                    }
                }
            }
            
            // Right Col (Urgent + Pomodoro)
            ColumnLayout {
                Layout.fillHeight: true
                Layout.preferredWidth: parent.width * 0.4
                
                // Urgent Card
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 60
                    color: Qt.rgba(0.9, 0.2, 0.2, 0.15)
                    radius: 8
                    border.color: "#ea4335"
                    border.width: 1
                    
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 6
                        PlasmaComponents.Label { 
                            text: "⚠ Urgente"
                            font.pixelSize: 10
                            color: "#ea4335"
                        }
                        PlasmaComponents.Label { 
                            text: urgentTask ? urgentTask.title : "Nada urgente"
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                            font.bold: true
                        }
                        PlasmaComponents.Label { 
                            text: urgentTask ? (urgentTask.days_left < 0 ? "Atrasado" : "En " + urgentTask.days_left + " días") : ""
                            font.pixelSize: 10
                        }
                    }
                }
                
                // Pomodoro
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: Qt.rgba(1,1,1,0.05)
                    radius: 8
                    
                    ColumnLayout {
                        anchors.centerIn: parent
                        PlasmaComponents.Label { text: "Pomodoro"; opacity: 0.5 }
                        PlasmaComponents.Label { 
                            text: {
                                var m = Math.floor(pomodoroSeconds / 60)
                                var s = pomodoroSeconds % 60
                                return (m < 10 ? "0"+m : m) + ":" + (s < 10 ? "0"+s : s)
                            }
                            font.pixelSize: 24
                            font.family: "Monospace"
                            font.bold: true
                        }
                        RowLayout {
                            PlasmaComponents.Button {
                                icon.name: pomodoroRunning ? "media-playback-pause" : "media-playback-start"
                                onClicked: pomodoroRunning = !pomodoroRunning
                            }
                            PlasmaComponents.Button {
                                icon.name: "view-refresh"
                                onClicked: {
                                    pomodoroRunning = false
                                    pomodoroSeconds = 1500
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    // Inner component for Stat Cards
    component StatCard : Rectangle {
        property int value: 0
        property string label: ""
        property color color: "white"
        
        Layout.fillWidth: true
        height: 50
        color: Qt.rgba(1,1,1,0.05)
        radius: 6
        
        ColumnLayout {
            anchors.centerIn: parent
            PlasmaComponents.Label {
                text: value
                font.bold: true
                font.pixelSize: 16
                color: parent.color
                Layout.alignment: Qt.AlignHCenter
            }
            PlasmaComponents.Label {
                text: label
                font.pixelSize: 10
                opacity: 0.7
                Layout.alignment: Qt.AlignHCenter
            }
        }
    }
}
