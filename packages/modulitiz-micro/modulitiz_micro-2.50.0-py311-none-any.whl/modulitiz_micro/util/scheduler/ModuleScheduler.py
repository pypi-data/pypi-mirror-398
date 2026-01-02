import schedule

from modulitiz_nano.ModuloListe import ModuloListe


class ModuleScheduler(object):
	@staticmethod
	def cancelJobByTag(tag:str):
		schedule.clear(tag)
	
	@classmethod
	def rescheduleJob(cls,tag:str,timeStr:str)->schedule.Job|None:
		# recupero il job
		jobs=schedule.get_jobs(tag)
		if ModuloListe.isEmpty(jobs):
			return None
		job=jobs[0]
		# cambio l'orario
		job.at(timeStr)
		# cancello quello vecchio
		cls.cancelJobByTag(tag)
		# lo aggiungo alla lista
		job.scheduler.jobs.append(job)
		# lo rischedulo
		job._schedule_next_run()
		return job
