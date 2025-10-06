import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import QtQuick.Window 2.15
Window {
    visible: true
    title: "Tree detection categories"
    visibility:  Window.Maximized 
        Text {
            id: text_topic
            text: "Tree detection categories"
            anchors.horizontalCenter: parent.horizontalCenter  // Center horizontally
            anchors.top: parent.top                             // Attach to top
            anchors.topMargin: 20 
            font.pixelSize: Screen.pixelDensity * 12   // scales with DPI
        }
        
    RowLayout {

        anchors.fill: parent   // Fill the whole window
        anchors.margins: 20
        spacing: 20

        Button {
            text: "Connect via Pi Camera"
            Layout.alignment: Qt.AlignHCenter
        }

        Button {
            text: "Connect via droid Camera"
            Layout.alignment: Qt.AlignHCenter
        }
    }
}