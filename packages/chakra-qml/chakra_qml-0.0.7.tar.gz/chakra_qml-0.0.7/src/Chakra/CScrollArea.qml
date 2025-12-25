pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls

/*
    CScrollArea - 可滚动容器组件

    == 组件库特有属性 ==
    size        : 滚动条尺寸，可选 "sm" | "md" | "lg"，默认 "md"
    horizontal  : 是否启用水平滚动，默认 false
    vertical    : 是否启用垂直滚动，默认 true
*/
Item {
    id: root

    property string size: "md"
    property bool horizontal: false
    property bool vertical: true

    default property alias content: contentItem.children

    readonly property alias flickable: flickableArea
    readonly property alias verticalScrollBar: vScrollBar
    readonly property alias horizontalScrollBar: hScrollBar

    readonly property bool showVertical: vertical
    readonly property bool showHorizontal: horizontal

    clip: true

    Flickable {
        id: flickableArea
        anchors.fill: parent
        contentWidth: root.showHorizontal ? contentItem.childrenRect.width : width
        contentHeight: root.showVertical ? contentItem.childrenRect.height : height
        boundsBehavior: Flickable.StopAtBounds
        boundsMovement: Flickable.StopAtBounds

        ScrollBar.vertical: vScrollBar
        ScrollBar.horizontal: hScrollBar

        Item {
            id: contentItem
            width: root.showHorizontal ? childrenRect.width : flickableArea.width
            height: root.showVertical ? childrenRect.height : flickableArea.height
        }
    }

    CScrollBar {
        id: vScrollBar
        visible: root.showVertical
        scrollBarSize: root.size
        orientation: Qt.Vertical
        policy: ScrollBar.AsNeeded
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: root.showHorizontal ? hScrollBar.top : parent.bottom
    }

    CScrollBar {
        id: hScrollBar
        visible: root.showHorizontal
        scrollBarSize: root.size
        orientation: Qt.Horizontal
        policy: ScrollBar.AsNeeded
        anchors.left: parent.left
        anchors.right: root.showVertical ? vScrollBar.left : parent.right
        anchors.bottom: parent.bottom
    }
}
