pragma ComponentBehavior: Bound

import QtQuick

/*
    CPagination - 分页器组件

    == 组件库特有属性 ==
    count          : 总数据条数，默认 1
    page           : 当前页码，默认 1
    pageSize       : 每页条数，默认 10
    siblingCount   : 当前页两侧显示的页码数，默认 1
    size           : 尺寸，可选 "sm" | "md" | "lg"，默认 "md"
    variant        : 变体，默认 "outline"
    colorScheme    : 颜色方案，默认 "primary"
    isCompact      : 是否紧凑模式，默认 false
    showsFirstLast : 是否显示首尾页按钮，默认 true

    == 信号 ==
    pageRequested(int newPage) : 请求翻页时触发
*/
Row {
    id: root

    property int count: 1
    property int page: 1
    property int pageSize: 10
    property int siblingCount: 1

    property string size: "md"
    property string variant: "outline"
    property string colorScheme: "primary"

    property bool isCompact: false
    property bool showsFirstLast: true

    signal pageRequested(int newPage)

    spacing: isCompact ? AppStyle.spacing2 : AppStyle.spacing1

    readonly property int totalPages: Math.max(1, Math.ceil(count / pageSize))
    readonly property int buttonSize: AppStyle.getButtonHeight(size)

    property var _cachedPageNumbers: []

    function goToPage(newPage) {
        if (newPage >= 1 && newPage <= totalPages && newPage !== page) {
            page = newPage;
            pageRequested(newPage);
        }
    }

    function generatePageNumbers() {
        let pages = [];
        const total = totalPages;
        const current = page;
        const siblings = siblingCount;

        if (total <= 7) {
            for (let i = 1; i <= total; i++) {
                pages.push(i);
            }
            return pages;
        }

        const leftSibling = Math.max(current - siblings, 1);
        const rightSibling = Math.min(current + siblings, total);

        const showLeftEllipsis = leftSibling > 2;
        const showRightEllipsis = rightSibling < total - 1;

        if (!showLeftEllipsis && showRightEllipsis) {
            const leftCount = 3 + 2 * siblings;
            for (let i = 1; i <= leftCount; i++) {
                pages.push(i);
            }
            pages.push(-1);
            pages.push(total);
        } else if (showLeftEllipsis && !showRightEllipsis) {
            pages.push(1);
            pages.push(-1);
            const rightCount = 3 + 2 * siblings;
            for (let i = total - rightCount + 1; i <= total; i++) {
                pages.push(i);
            }
        } else {
            pages.push(1);
            pages.push(-1);
            for (let i = leftSibling; i <= rightSibling; i++) {
                pages.push(i);
            }
            pages.push(-2);
            pages.push(total);
        }

        return pages;
    }

    function updatePageNumbers() {
        _cachedPageNumbers = generatePageNumbers();
    }

    onTotalPagesChanged: updatePageNumbers()
    onPageChanged: updatePageNumbers()
    onSiblingCountChanged: updatePageNumbers()
    Component.onCompleted: updatePageNumbers()

    CButton {
        visible: root.showsFirstLast && !root.isCompact
        leftIcon: "arrow-line-left"
        size: root.size
        variant: root.variant
        colorScheme: root.colorScheme
        width: visible ? root.buttonSize : 0
        height: root.buttonSize
        enabled: root.page > 1
        iconOnly: true
        onClicked: root.goToPage(1)
    }

    CButton {
        visible: !root.isCompact
        leftIcon: "caret-left"
        size: root.size
        variant: root.variant
        colorScheme: root.colorScheme
        width: visible ? root.buttonSize : 0
        height: root.buttonSize
        enabled: root.page > 1
        iconOnly: true
        onClicked: root.goToPage(root.page - 1)
    }

    Row {
        spacing: root.spacing
        visible: !root.isCompact

        Repeater {
            model: root._cachedPageNumbers

            delegate: Item {
                id: delegateItem
                required property int modelData
                required property int index

                width: root.buttonSize
                height: root.buttonSize

                CButton {
                    visible: delegateItem.modelData !== -1 && delegateItem.modelData !== -2
                    text: delegateItem.modelData.toString()
                    size: root.size
                    variant: delegateItem.modelData === root.page ? "solid" : root.variant
                    colorScheme: root.colorScheme
                    width: root.buttonSize
                    height: root.buttonSize
                    onClicked: root.goToPage(delegateItem.modelData)
                }

                Text {
                    visible: delegateItem.modelData === -1 || delegateItem.modelData === -2
                    text: "..."
                    anchors.centerIn: parent
                    font.pixelSize: AppStyle.getFontSize(root.size === "lg" ? "md" : "sm")
                    color: AppStyle.textSecondary
                }
            }
        }
    }

    Rectangle {
        visible: root.isCompact
        width: pageText.width + AppStyle.spacing3 * 2
        height: root.buttonSize
        radius: AppStyle.radiusMd
        color: "transparent"
        border.width: 1
        border.color: AppStyle.borderColor

        Text {
            id: pageText
            anchors.centerIn: parent
            text: root.page + " / " + root.totalPages
            font.pixelSize: AppStyle.getFontSize(root.size === "lg" ? "md" : "sm")
            color: AppStyle.textColor
        }
    }

    CButton {
        visible: !root.isCompact
        rightIcon: "caret-right"
        size: root.size
        variant: root.variant
        colorScheme: root.colorScheme
        width: visible ? root.buttonSize : 0
        height: root.buttonSize
        enabled: root.page < root.totalPages
        iconOnly: true
        onClicked: root.goToPage(root.page + 1)
    }

    CButton {
        visible: root.showsFirstLast && !root.isCompact
        rightIcon: "arrow-line-right"
        size: root.size
        variant: root.variant
        colorScheme: root.colorScheme
        width: visible ? root.buttonSize : 0
        height: root.buttonSize
        enabled: root.page < root.totalPages
        iconOnly: true
        onClicked: root.goToPage(root.totalPages)
    }
}
