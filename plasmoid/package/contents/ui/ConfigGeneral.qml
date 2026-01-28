import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import org.kde.kirigami 2.20 as Kirigami
import org.kde.kquickcontrols 2.0 as KQControls

Kirigami.FormLayout {
    
    // Alias properties to the settings defined in main.xml
    // The property name must match "cfg_" + entry name
    property alias cfg_dodgeWindows: dodgeCheckbox.checked
    property alias cfg_backgroundOpacity: opacitySlider.value

    CheckBox {
        id: dodgeCheckbox
        text: "Esquivar Ventanas (Dodge Windows)"
        Kirigami.FormData.label: "Comportamiento:"
    }

    RowLayout {
        Kirigami.FormData.label: "Opacidad del Fondo:"
        
        Slider {
            id: opacitySlider
            from: 0.0
            to: 1.0
            stepSize: 0.05
            Layout.fillWidth: true
        }
        
        Label {
            text: Math.round(opacitySlider.value * 100) + "%"
            Layout.preferredWidth: 40
        }
    }
}
