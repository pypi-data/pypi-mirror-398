import QtQuick

/*
    CMenuSeparator - 菜单分隔线组件

    == 组件库特有属性 ==
    topMargin    : 上边距，默认 AppStyle.spacing1
    bottomMargin : 下边距，默认 AppStyle.spacing1
*/
Rectangle {
    id: root

    implicitWidth: parent ? parent.width : 100
    implicitHeight: 1 + topMargin + bottomMargin

    property int topMargin: AppStyle.spacing1
    property int bottomMargin: AppStyle.spacing1

    color: "transparent"

    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.leftMargin: AppStyle.spacing2
        anchors.rightMargin: AppStyle.spacing2
        anchors.verticalCenter: parent.verticalCenter
        height: 1
        color: AppStyle.borderColor
    }
}
