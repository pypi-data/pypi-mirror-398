import QtQuick
import QtQuick.Controls

/*
    CScrollBar - 滚动条组件

    == 组件库特有属性 ==
    scrollBarSize : 尺寸，可选 "xs" | "sm" | "md" | "lg"，默认 "md"
*/
ScrollBar {
    id: control

    property string scrollBarSize: "md"

    readonly property var _scrollBarWidths: ({ "xs": 6, "sm": 8, "md": 10, "lg": 12 })
    readonly property var _scrollBarPaddings: ({ "xs": 1, "sm": 2, "md": 2, "lg": 3 })

    readonly property int scrollBarWidth: _scrollBarWidths[scrollBarSize] || 10
    readonly property int scrollBarPadding: _scrollBarPaddings[scrollBarSize] || 2

    implicitWidth: orientation === Qt.Vertical ? scrollBarWidth : 100
    implicitHeight: orientation === Qt.Horizontal ? scrollBarWidth : 100

    padding: scrollBarPadding
    visible: size < 1.0
    minimumSize: 0.1

    Component.onCompleted: {
        var win = control.Window.window
        if (win && win.framelessInstance && win.framelessInstance.setHitTestVisible) {
            win.framelessInstance.setHitTestVisible(control)
        }
    }

    contentItem: Rectangle {
        radius: AppStyle.radiusFull
        color: {
            if (control.pressed)
                return AppStyle.isDark ? Qt.rgba(255, 255, 255, 0.48) : Qt.rgba(0, 0, 0, 0.48);
            if (control.hovered)
                return AppStyle.isDark ? Qt.rgba(255, 255, 255, 0.36) : Qt.rgba(0, 0, 0, 0.36);
            return AppStyle.isDark ? Qt.rgba(255, 255, 255, 0.24) : Qt.rgba(0, 0, 0, 0.24);
        }

        Behavior on color {
            ColorAnimation {
                duration: AppStyle.durationFast
                easing.type: Easing.OutCubic
            }
        }

        opacity: control.active || control.hovered ? 1 : 0.6

        Behavior on opacity {
            NumberAnimation {
                duration: AppStyle.durationNormal
                easing.type: Easing.OutCubic
            }
        }
    }

    background: Rectangle {
        color: "transparent"
        radius: AppStyle.radiusFull
    }
}
