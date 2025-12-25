pragma ComponentBehavior: Bound

import QtQuick

/*
    CBox - 盒子布局组件

    == 组件库特有属性 ==

    内边距属性:
    padding           : 内边距（四边），默认 0
    paddingX          : 水平内边距，默认等于 padding
    paddingY          : 垂直内边距，默认等于 padding
    paddingTop        : 上内边距
    paddingBottom     : 下内边距
    paddingLeft       : 左内边距
    paddingRight      : 右内边距

    其他属性:
    margin            : 外边距，默认 0
    backgroundColor   : 背景色
    borderWidth       : 边框宽度
    borderColor       : 边框颜色
    cornerRadius      : 圆角半径
*/
Rectangle {
    id: root

    // 内边距
    property int padding: 0
    property int paddingX: padding
    property int paddingY: padding
    property int paddingTop: paddingY
    property int paddingBottom: paddingY
    property int paddingLeft: paddingX
    property int paddingRight: paddingX

    // 外边距
    property int margin: 0

    // 样式属性
    property alias backgroundColor: root.color

    // 边框属性
    property int borderWidth: 0
    property color borderColor: "transparent"
    property int cornerRadius: 0

    // 默认透明
    color: "transparent"
    border.width: borderWidth
    border.color: borderColor
    radius: cornerRadius

    // 内容区域
    default property alias content: contentContainer.data

    Item {
        id: contentContainer
        anchors.fill: parent
        anchors.topMargin: root.paddingTop
        anchors.bottomMargin: root.paddingBottom
        anchors.leftMargin: root.paddingLeft
        anchors.rightMargin: root.paddingRight

        // 自动设置子元素宽度
        Component.onCompleted: AppStyle.updateChildrenWidth(contentContainer, contentContainer.width)
        onChildrenChanged: AppStyle.updateChildrenWidth(contentContainer, contentContainer.width)
        onWidthChanged: AppStyle.updateChildrenWidth(contentContainer, contentContainer.width)
    }
}
