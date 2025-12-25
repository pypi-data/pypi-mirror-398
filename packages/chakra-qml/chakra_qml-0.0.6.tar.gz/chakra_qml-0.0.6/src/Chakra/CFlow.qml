pragma ComponentBehavior: Bound

import QtQuick

/*
    CFlow - 流式布局组件（Flow 增强版）

    == 组件库特有属性 ==
    direction : 排列方向，可选 "row" | "column"，默认 "row"
    justify   : 主轴对齐，可选 "start" | "center" | "end"，默认 "start"
    spacing   : 子元素间距，默认 0
    padding   : 内边距（四边），默认 0
    paddingX  : 水平内边距
    paddingY  : 垂直内边距
*/
Item {
    id: root

    property string direction: "row"
    property string justify: "start"
    property int spacing: 0
    property int padding: 0
    property int paddingX: padding
    property int paddingY: padding

    default property alias content: flowLayout.children

    implicitWidth: flowLayout.implicitWidth + paddingX * 2
    implicitHeight: flowLayout.implicitHeight + paddingY * 2

    Flow {
        id: flowLayout

        anchors.fill: parent
        anchors.margins: root.padding
        anchors.leftMargin: root.paddingX
        anchors.rightMargin: root.paddingX
        anchors.topMargin: root.paddingY
        anchors.bottomMargin: root.paddingY

        flow: root.direction === "column" ? Flow.TopToBottom : Flow.LeftToRight
        spacing: root.spacing

        width: root.direction === "row" ? parent.width : undefined
        height: root.direction === "column" ? parent.height : undefined

        anchors.horizontalCenter: {
            if (root.direction === "row" && root.justify === "center") {
                return parent.horizontalCenter;
            }
            return undefined;
        }

        anchors.right: {
            if (root.direction === "row" && root.justify === "end") {
                return parent.right;
            }
            return undefined;
        }

        anchors.verticalCenter: {
            if (root.direction === "column" && root.justify === "center") {
                return parent.verticalCenter;
            }
            return undefined;
        }

        anchors.bottom: {
            if (root.direction === "column" && root.justify === "end") {
                return parent.bottom;
            }
            return undefined;
        }
    }
}
