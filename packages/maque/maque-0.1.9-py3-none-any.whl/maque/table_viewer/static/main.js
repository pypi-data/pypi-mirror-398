const { createApp } = Vue;
const { ElMessage, ElMessageBox } = ElementPlus;

createApp({
    data() {
        return {
            loading: false,
            tableInfo: null,
            tableData: {
                data: [],
                total: 0,
                page: 1,
                page_size: 100,
                total_pages: 0
            },
            pagination: {
                currentPage: 1,
                pageSize: 100
            },
            sortConfig: {
                prop: null,
                order: null
            },
            activeFilters: [],
            showFilterDialog: false,
            filterConfigs: [],
            
            // 列显示控制
            showColumnDialog: false,
            visibleColumns: [],
            allColumns: [],
            
            // 编辑相关
            editingCell: null,
            editingValue: '',
            
            // 图片预览
            showImagePreview: false,
            currentImageUrl: '',
            currentImageList: [], // 当前行的所有图片列表
            currentImageIndex: 0, // 当前显示的图片索引
            
            // 文件上传
            showUploadDialog: false,
            isDragOver: false,
            
            // 图像尺寸设置
            imageSize: 'medium', // small, medium, large, xlarge
            
            // 图像分隔符设置
            imageSeparator: 'auto', // auto, comma, semicolon, newline, custom
            customSeparator: '', // 自定义分隔符
            
            // 图像加载状态管理
            loadedImages: new Set() // 存储已成功加载的图像URL
        };
    },
    
    computed: {
        tableColumns() {
            // 如果有列筛选，使用筛选后的列，否则使用全部列
            if (this.visibleColumns.length > 0) {
                return this.visibleColumns;
            }
            return this.tableInfo ? this.tableInfo.columns : [];
        },
        
        // 计算当前图像尺寸
        currentImageSizes() {
            const sizeMap = {
                'small': { width: 80, height: 60 },
                'medium': { width: 120, height: 90 },
                'large': { width: 160, height: 120 },
                'xlarge': { width: 200, height: 150 },
                'xxlarge': { width: 400, height: 300 }
            };
            return sizeMap[this.imageSize] || sizeMap.medium;
        }
    },
    
    async mounted() {
        // 加载保存的设置
        this.loadImageSizeFromStorage();
        this.loadSeparatorFromStorage();
        
        // 初始化CSS变量
        this.updateImageSizeCss();
        
        await this.loadTableInfo();
        await this.loadTableData();
    },
    
    methods: {
        // 加载表格信息
        async loadTableInfo() {
            try {
                const response = await fetch('/api/table/info');
                this.tableInfo = await response.json();
                // 初始化列数据
                if (this.tableInfo && this.tableInfo.columns) {
                    this.allColumns = [...this.tableInfo.columns];
                    if (this.visibleColumns.length === 0) {
                        this.visibleColumns = [...this.tableInfo.columns];
                    }
                }
            } catch (error) {
                ElMessage.error('加载表格信息失败: ' + error.message);
            }
        },
        
        // 加载表格数据
        async loadTableData() {
            this.loading = true;
            try {
                const params = new URLSearchParams({
                    page: this.pagination.currentPage,
                    page_size: this.pagination.pageSize
                });
                
                if (this.sortConfig.prop) {
                    params.append('sort_by', this.sortConfig.prop);
                    params.append('sort_order', this.sortConfig.order === 'ascending' ? 'asc' : 'desc');
                }
                
                if (this.activeFilters.length > 0) {
                    params.append('filters', JSON.stringify(this.activeFilters));
                }
                
                // 添加列筛选参数
                if (this.visibleColumns.length > 0 && this.visibleColumns.length < this.allColumns.length) {
                    params.append('visible_columns', JSON.stringify(this.visibleColumns));
                }
                
                // 添加分隔符参数
                if (this.imageSeparator !== 'auto') {
                    let separator = '';
                    switch (this.imageSeparator) {
                        case 'semicolon':
                            separator = ';';
                            break;
                        case 'newline':
                            separator = '\\n';  // 使用字符串形式
                            break;
                        case 'custom':
                            separator = this.customSeparator;
                            break;
                    }
                    if (separator) {
                        params.append('separator', separator);
                    }
                }
                
                const response = await fetch(`/api/table/data?${params}`);
                this.tableData = await response.json();
                
                // 更新可见列（如果后端返回了）
                if (this.tableData.visible_columns) {
                    this.visibleColumns = this.tableData.visible_columns;
                }
            } catch (error) {
                ElMessage.error('加载数据失败: ' + error.message);
            } finally {
                this.loading = false;
            }
        },
        
        // 刷新数据
        async refreshData() {
            await this.loadTableInfo();
            await this.loadTableData();
            ElMessage.success('数据已刷新');
        },
        
        // 排序处理
        handleSort(column, direction) {
            if (this.sortConfig.prop === column && 
                this.sortConfig.order === (direction === 'asc' ? 'ascending' : 'descending')) {
                // 如果点击的是当前排序列和方向，则清除排序
                this.sortConfig = { prop: null, order: null };
            } else {
                // 设置新的排序
                this.sortConfig = { 
                    prop: column, 
                    order: direction === 'asc' ? 'ascending' : 'descending' 
                };
            }
            this.pagination.currentPage = 1;
            this.loadTableData();
        },
        
        // 分页处理
        handleSizeChange(size) {
            this.pagination.pageSize = size;
            this.pagination.currentPage = 1;
            this.loadTableData();
        },
        
        handleCurrentChange(page) {
            this.pagination.currentPage = page;
            this.loadTableData();
        },
        
        // 判断是否为图片列
        isImageColumn(column) {
            return this.tableInfo && this.tableInfo.image_columns.includes(column);
        },
        
        // 获取列宽度
        getColumnWidth(column) {
            if (this.isImageColumn(column)) {
                // 根据图像尺寸动态调整列宽，预留3张图片的空间 + 边距
                const imageWidth = this.currentImageSizes.width;
                return Math.max(imageWidth * 3 + 40, 250); // 最小250px
            }
            return null;
        },
        
        
        // 检查图像是否已加载
        isImageLoaded(imageUrl) {
            return this.loadedImages.has(imageUrl);
        },
        
        // 图像加载成功处理
        onImageLoadSuccess(imageUrl) {
            this.loadedImages.add(imageUrl);
            this.$forceUpdate(); // 强制更新视图
        },
        
        // 图像加载失败处理
        onImageLoadError(imageUrl) {
            this.loadedImages.delete(imageUrl);
        },
        
        // 筛选相关
        addFilter() {
            this.filterConfigs.push({
                column: '',
                operator: 'contains',
                value: ''
            });
        },
        
        removeFilter(index) {
            this.filterConfigs.splice(index, 1);
        },
        
        addColumnFilter(column) {
            this.filterConfigs.push({
                column: column,
                operator: 'contains',
                value: ''
            });
            this.showFilterDialog = true;
        },
        
        applyFilters() {
            this.activeFilters = this.filterConfigs.filter(f => f.column && f.value);
            this.pagination.currentPage = 1;
            this.showFilterDialog = false;
            this.loadTableData();
        },
        
        clearFilters() {
            this.activeFilters = [];
            this.filterConfigs = [];
            this.pagination.currentPage = 1;
            this.loadTableData();
        },
        
        // 列管理相关
        applyColumnFilter() {
            this.pagination.currentPage = 1;
            this.showColumnDialog = false;
            this.loadTableData();
        },
        
        resetColumns() {
            this.visibleColumns = [...this.allColumns];
            this.applyColumnFilter();
        },
        
        selectAllColumns() {
            this.visibleColumns = [...this.allColumns];
        },
        
        selectNoColumns() {
            this.visibleColumns = [];
        },
        
        toggleColumn(column) {
            const index = this.visibleColumns.indexOf(column);
            if (index > -1) {
                this.visibleColumns.splice(index, 1);
            } else {
                this.visibleColumns.push(column);
            }
        },
        
        // 编辑相关
        startEdit(row, column, value) {
            if (this.isImageColumn(column)) return;
            
            this.editingCell = { row, column };
            this.editingValue = value || '';
            
            this.$nextTick(() => {
                const input = this.$refs.cellInput;
                if (input && input[0]) {
                    input[0].focus();
                }
            });
        },
        
        async saveCell(rowIndex, column) {
            try {
                const response = await fetch(`/api/table/cell/${rowIndex}/${column}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ value: this.editingValue })
                });
                
                let result;
                try {
                    result = await response.json();
                } catch (jsonError) {
                    ElMessage.error('更新失败: 服务器返回了无效的响应');
                    return;
                }
                
                // 检查HTTP状态码
                if (!response.ok) {
                    const errorMsg = result?.detail || result?.message || `HTTP ${response.status}`;
                    ElMessage.error('更新失败: ' + errorMsg);
                    return;
                }
                
                if (result && result.success) {
                    await this.loadTableData();
                    ElMessage.success('更新成功');
                } else {
                    const errorMsg = result?.message || '操作失败';
                    ElMessage.error('更新失败: ' + errorMsg);
                }
            } catch (error) {
                console.error('Save cell error:', error);
                let errorMsg = '网络错误';
                if (error instanceof Error) {
                    errorMsg = error.message;
                } else if (typeof error === 'string') {
                    errorMsg = error;
                } else if (error && error.message) {
                    errorMsg = error.message;
                } else if (error && typeof error === 'object') {
                    errorMsg = JSON.stringify(error);
                }
                ElMessage.error('更新失败: ' + errorMsg);
            } finally {
                this.editingCell = null;
                this.editingValue = '';
            }
        },
        
        cancelEdit() {
            this.editingCell = null;
            this.editingValue = '';
        },
        
        // 图片相关
        showImageDialog(imageUrl, allImagesData, clickedIndex) {
            // 如果提供了完整的图片数据和索引，设置图片列表
            if (allImagesData !== undefined && clickedIndex !== undefined) {
                // allImagesData 现在是后端已处理好的 paths 数组
                if (Array.isArray(allImagesData)) {
                    this.currentImageList = allImagesData;
                } else {
                    // 兼容旧版本：如果传入的是字符串，使用简单切分逻辑
                    var paths = allImagesData.split(/[,;]+/);
                    var imagePaths = [];
                    for (var i = 0; i < paths.length; i++) {
                        var path = paths[i].trim();
                        if (path) imagePaths.push(path);
                    }
                    this.currentImageList = imagePaths;
                }
                this.currentImageIndex = clickedIndex;
            } else {
                // 兼容单图片模式
                this.currentImageList = [imageUrl];
                this.currentImageIndex = 0;
            }
            
            this.currentImageUrl = imageUrl;
            this.showImagePreview = true;
        },
        
        // 显示上一张图片
        showPreviousImage: function() {
            if (this.currentImageIndex > 0) {
                this.currentImageIndex--;
                this.currentImageUrl = this.currentImageList[this.currentImageIndex];
            }
        },
        
        // 显示下一张图片
        showNextImage: function() {
            if (this.currentImageIndex < this.currentImageList.length - 1) {
                this.currentImageIndex++;
                this.currentImageUrl = this.currentImageList[this.currentImageIndex];
            }
        },
        
        handleImageError(event) {
            event.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjE1MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjE1MCIgZmlsbD0iI2Y1ZjVmNSIvPjx0ZXh0IHg9IjEwMCIgeT0iNzUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPuWbvueJh+WKoOi9veWksei0pTwvdGV4dD48L3N2Zz4=';
        },
        
        // 表格操作
        async saveTable() {
            try {
                const response = await fetch('/api/table/save', { method: 'POST' });
                let result;
                try {
                    result = await response.json();
                } catch (jsonError) {
                    ElMessage.error('保存失败: 服务器返回了无效的响应');
                    return;
                }
                
                if (!response.ok) {
                    const errorMsg = result?.detail || result?.message || `HTTP ${response.status}`;
                    ElMessage.error('保存失败: ' + errorMsg);
                    return;
                }
                
                if (result && result.success) {
                    ElMessage.success('保存成功');
                } else {
                    const errorMsg = result?.message || '操作失败';
                    ElMessage.error('保存失败: ' + errorMsg);
                }
            } catch (error) {
                console.error('Save table error:', error);
                let errorMsg = '网络错误';
                if (error instanceof Error) {
                    errorMsg = error.message;
                } else if (typeof error === 'string') {
                    errorMsg = error;
                } else if (error && error.message) {
                    errorMsg = error.message;
                } else if (error && typeof error === 'object') {
                    errorMsg = JSON.stringify(error);
                }
                ElMessage.error('保存失败: ' + errorMsg);
            }
        },
        
        async resetTable() {
            try {
                await ElMessageBox.confirm('确定要重置表格到原始状态吗？这将丢失所有未保存的修改。', '确认重置', {
                    type: 'warning'
                });
                
                const response = await fetch('/api/table/reset', { method: 'POST' });
                let result;
                try {
                    result = await response.json();
                } catch (jsonError) {
                    ElMessage.error('重置失败: 服务器返回了无效的响应');
                    return;
                }
                
                if (!response.ok) {
                    const errorMsg = result?.detail || result?.message || `HTTP ${response.status}`;
                    ElMessage.error('重置失败: ' + errorMsg);
                    return;
                }
                
                if (result && result.success) {
                    await this.loadTableData();
                    ElMessage.success('重置成功');
                } else {
                    const errorMsg = result?.message || '操作失败';
                    ElMessage.error('重置失败: ' + errorMsg);
                }
            } catch (error) {
                if (error !== 'cancel') {
                    console.error('Reset table error:', error);
                    let errorMsg = '网络错误';
                    if (error instanceof Error) {
                        errorMsg = error.message;
                    } else if (typeof error === 'string') {
                        errorMsg = error;
                    } else if (error && error.message) {
                        errorMsg = error.message;
                    } else if (error && typeof error === 'object') {
                        errorMsg = JSON.stringify(error);
                    }
                    ElMessage.error('重置失败: ' + errorMsg);
                }
            }
        },
        
        // 图像尺寸相关
        onImageSizeChange() {
            // 保存到本地存储
            try {
                localStorage.setItem('maque_table_viewer_image_size', this.imageSize);
            } catch (e) {
                // 忽略localStorage错误
            }
            
            // 更新CSS变量
            this.updateImageSizeCss();
            
            // 强制表格重新计算列宽
            this.$nextTick(() => {
                // 通过改变一个响应式属性触发表格重新渲染
                const temp = this.tableData.data;
                this.tableData.data = [];
                this.$nextTick(() => {
                    this.tableData.data = temp;
                });
            });
        },
        
        updateImageSizeCss() {
            const sizes = this.currentImageSizes;
            const root = document.documentElement;
            root.style.setProperty('--image-width', sizes.width + 'px');
            root.style.setProperty('--image-height', sizes.height + 'px');
        },
        
        loadImageSizeFromStorage() {
            try {
                const saved = localStorage.getItem('maque_table_viewer_image_size');
                if (saved && ['small', 'medium', 'large', 'xlarge', 'xxlarge'].includes(saved)) {
                    this.imageSize = saved;
                }
            } catch (e) {
                // 忽略localStorage错误
            }
        },
        
        // 分隔符相关方法
        async onSeparatorChange() {
            console.log('分隔符改变:', this.imageSeparator);
            
            // 保存到本地存储
            this.saveSeparatorToStorage();
            
            // 清空图像加载状态
            this.loadedImages.clear();
            
            // 重新加载数据，使用新的分隔符设置
            console.log('开始重新加载数据...');
            try {
                await this.loadTableData();
                console.log('数据重新加载完成');
            } catch (error) {
                console.error('数据重新加载失败:', error);
                ElMessage.error('重新加载数据失败: ' + error.message);
                // 不要清空现有数据，保持用户能看到之前的内容
            }
        },
        
        saveSeparatorToStorage() {
            try {
                localStorage.setItem('maque_table_viewer_separator', this.imageSeparator);
                if (this.customSeparator) {
                    localStorage.setItem('maque_table_viewer_custom_separator', this.customSeparator);
                }
            } catch (e) {
                // 忽略localStorage错误
            }
        },
        
        loadSeparatorFromStorage() {
            try {
                const savedSeparator = localStorage.getItem('maque_table_viewer_separator');
                if (savedSeparator && ['auto', 'semicolon', 'newline', 'custom'].includes(savedSeparator)) {
                    this.imageSeparator = savedSeparator;
                }
                
                const savedCustom = localStorage.getItem('maque_table_viewer_custom_separator');
                if (savedCustom) {
                    this.customSeparator = savedCustom;
                }
            } catch (e) {
                // 忽略localStorage错误
            }
        },
        
        // 文件上传相关方法
        triggerFileInput() {
            this.$refs.fileInput.click();
        },
        
        handleDragOver(event) {
            event.preventDefault();
            this.isDragOver = true;
        },
        
        handleDragLeave(event) {
            event.preventDefault();
            this.isDragOver = false;
        },
        
        async handleFileDrop(event) {
            event.preventDefault();
            this.isDragOver = false;
            
            const files = event.dataTransfer.files;
            if (files.length > 0) {
                await this.uploadFile(files[0]);
            }
        },
        
        async handleFileSelect(event) {
            const files = event.target.files;
            if (files.length > 0) {
                await this.uploadFile(files[0]);
            }
        },
        
        async uploadFile(file) {
            // 检查文件类型
            const allowedTypes = ['.xlsx', '.xls', '.csv'];
            const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
            
            if (!allowedTypes.includes(fileExtension)) {
                ElMessage.error('不支持的文件格式，请选择 .xlsx, .xls 或 .csv 文件');
                return;
            }
            
            this.loading = true;
            
            try {
                const formData = new FormData();
                formData.append('file', file);
                
                const response = await fetch('/api/table/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    ElMessage.success('文件上传成功，正在加载数据...');
                    this.showUploadDialog = false;
                    
                    // 重新加载表格信息和数据
                    await this.loadTableInfo();
                    await this.loadTableData();
                } else {
                    ElMessage.error('上传失败: ' + result.message);
                }
            } catch (error) {
                ElMessage.error('上传失败: ' + error.message);
            } finally {
                this.loading = false;
                // 清空文件输入
                this.$refs.fileInput.value = '';
            }
        }
    }
}).use(ElementPlus).mount('#app');