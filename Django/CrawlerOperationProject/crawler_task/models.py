from django.db import models
from django.utils import timezone

class BossSpiderTask(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILURE', 'Failure'),
    ]

    # 任务参数
    domain = models.CharField(max_length=255, help_text="Target domain for the spider.")
    city = models.CharField(max_length=100, help_text="Target city for the spider.")
    count = models.IntegerField(help_text="Number of items to scrape.")
    query = models.CharField(max_length=255, help_text="Query for the spider.")

    # 任务状态与结果
    create_time = models.DateTimeField(auto_now_add=True, help_text="Time when the task was created.")
    update_time = models.DateTimeField(auto_now=True, help_text="Time when the task status was last updated.")  # 调用 save() 方法时，自动设置为当前时间
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', help_text="Current status of the task.")
    result = models.TextField(blank=True, help_text="Result data returned by the spider (e.g., JSON).")
    exception = models.TextField(blank=True, help_text="Exception message if the task failed.")

    # Celery Task ID (用于关联 Celery 任务)
    task_id = models.CharField(max_length=255, blank=True, help_text="Celery task ID associated with this entry.")

    def __str__(self):
        return f"Task {self.id} - {self.domain} - {self.city} - {self.count} - {self.query}"

    class Meta:
        db_table = 'boss_spider_task'       # 指定数据库表名
        ordering = ['-create_time']         # 默认按创建时间倒序排列

class BossSpiderItems(models.Model):
    # id = models.AutoField(primary_key=True) # Django 默认会创建名为 'id' 的主键
    name = models.CharField(max_length=255, help_text='职位名称')
    link = models.URLField(max_length=500, db_index=True, blank=True, null=True, help_text='岗位详情页URL') # URLField 更合适
    boss_name = models.CharField(max_length=100, blank=True, null=True, help_text='招聘者姓名')
    boss_title = models.CharField(max_length=100, blank=True, null=True, help_text='招聘者职位')
    salary = models.CharField(max_length=100, blank=True, null=True, help_text='薪资范围')
    skills = models.TextField(blank=True, null=True, help_text='技能标签 (逗号分隔的字符串)') # 存储处理后的字符串
    experience = models.CharField(max_length=100, blank=True, null=True, help_text='工作经验')
    degree = models.CharField(max_length=50, blank=True, null=True, help_text='学历要求')
    city = models.CharField(max_length=50, blank=True, null=True, help_text='城市')
    area = models.CharField(max_length=50, blank=True, null=True, help_text='区域')
    address = models.CharField(max_length=50, blank=True, null=True, help_text='详细地址')
    company = models.CharField(max_length=255, blank=True, null=True, help_text='公司名称')
    scale = models.CharField(max_length=100, blank=True, null=True, help_text='公司规模')
    welfare = models.TextField(blank=True, null=True, help_text='公司福利 (逗号分隔的字符串)') # 存储处理后的字符串
    # description = models.TextField(blank=True, null=True, help_text='职位描述')
    # address_detail = models.CharField(max_length=255, blank=True, null=True, help_text='详细地址')
    created_at = models.DateTimeField(auto_now_add=True, help_text='创建时间')
    updated_at = models.DateTimeField(auto_now=True, help_text='最后更新时间')

    class Meta:
        abstract = True

    def __str__(self):
        return f"Job Item: {self.name} - {self.link}"

class BossSpiderResults(BossSpiderItems):
    # 新增 task_id 字段
    task_id = models.CharField(max_length=255, blank=True, help_text="Celery task ID associated with this entry.")

    class Meta:
        db_table = 'boss_spider_results' # 指定子类模型的数据库表名

    def __str__(self):
        return f"Job Task Result: {self.name} - {self.link} (Task: {self.task_id})"

class BossSpiderResultsBeat(BossSpiderItems):
    class Meta:
        db_table = 'boss_spider_results_beat'  # 指定数据库表名
    def __str__(self):
        return f"Job Beat Result: {self.name} - {self.link}"